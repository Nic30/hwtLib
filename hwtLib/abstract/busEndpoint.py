from builtins import isinstance
from copy import copy
from math import ceil
from typing import Union, Tuple, Type

from hwt.code import Switch, Concat
from hwt.constants import INTF_DIRECTION
from hwt.hObjList import HObjList
from hwt.hdl.frameTmpl import FrameTmpl
from hwt.hdl.transTmpl import TransTmpl
from hwt.hdl.types.array import HArray
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.hdlType import HdlType
from hwt.hdl.types.struct import HStruct, HStructField
from hwt.hdl.types.structUtils import field_path_get_type, HdlType_select
from hwt.hwIO import HwIO
from hwt.hwIOs.hwIOStruct import HwIOStruct
from hwt.hwIOs.hwIOUnion import HwIOUnionSink, HwIOUnionSource
from hwt.hwIOs.hwIO_map import HwIOObjMap_get_by_field_path, HwIOObjMap, \
    walkHwIOStructAndHwIOObjMap, HTypeFromHwIOObjMap
from hwt.hwIOs.std import HwIOBramPort_noClk, HwIORegCntrl, HwIOSignal, HwIODataVld
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.mainBases import RtlSignalBase
from hwt.math import log2ceil, inRange, isPow2
from hwt.pyUtils.typingFuture import override
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.typePath import TypePath
from hwtLib.abstract.addressStepTranslation import AddressStepTranslation
from ipCorePackager.constants import DIRECTION


def TransTmpl_get_min_addr(t: TransTmpl):
    if not t.children:
        return t.bitAddr
    elif isinstance(t.children, list) and t.children:
        for c in t.children:
            r = TransTmpl_get_min_addr(c)
            if r is not None:
                return r
        return None
    else:
        return TransTmpl_get_min_addr(t.children)


def TransTmpl_get_max_addr(t: TransTmpl):
    if t.itemCnt is None:
        offset = 0
    else:
        item_size = t.bit_length() // t.itemCnt
        offset = t.bitAddr + (t.itemCnt - 1) * item_size

    if not t.children:
        return t.bitAddrEnd
    elif isinstance(t.children, list) and t.children:
        for c in reversed(t.children):
            r = TransTmpl_get_max_addr(c)
            if r is not None:
                return offset + r
        return None
    else:
        return offset + TransTmpl_get_max_addr(t.children)


class BusEndpoint(HwModule):
    """
    Abstract unit

    Delegate request from bus to fields of structure
    (fields are represented by various interfaces)
    write has higher priority

    :note: implementation is usually address decoder


    .. figure:: ./_static/BusEndpoint.png

    """

    def __init__(self, structTemplate, hwIOCls:Type[HwIO]=None, shouldEnterFn=None):
        """
        :param structTemplate: instance of HStruct which describes
            address space of this endpoint
        :param hwIOCls: class of bus interface which should be used
        :param shouldEnterFn: function(root_t, structFieldPath) return (shouldEnter, shouldUse)
            where shouldEnter is flag that means iterator over this interface
            should look inside of this actual object
            and shouldUse flag means that this field should be used
            (to create interface)
        """
        assert hwIOCls is not None, "hwIOCls has to be specified"

        self._hwIOCls = hwIOCls
        self.STRUCT_TEMPLATE = structTemplate
        if shouldEnterFn is None:
            self.shouldEnterFn = self._defaultShouldEnterFn
        else:
            self.shouldEnterFn = shouldEnterFn
        HwModule.__init__(self)

    @staticmethod
    def _defaultShouldEnterFn(root: HdlType, field_path: Tuple[Union[str, int]]):
        """
        Default method which resolves how the parts of input data type
        should be represented on interface level.
        """
        t = field_path_get_type(root, field_path)
        isNonPrimitiveArray = isinstance(t, HArray) and\
            not isinstance(t.element_t, HBits)
        shouldEnter = isinstance(t, HStruct) or isNonPrimitiveArray
        shouldUse = not shouldEnter
        return shouldEnter, shouldUse

    def _getWordAddrStep(self) -> int:
        """
        :return: how many address units is one word on bus (e.g. 32b AXI -> 4)
        """
        raise NotImplementedError(
            "Should be overridden in concrete implementation, this is abstract class")

    def _getAddrStep(self) -> int:
        """
        :return: how many bits does 1 address unit addresses, (e.g. AXI -> 8b, index to uint32_t[N] -> 32)
        """
        raise NotImplementedError(
            "Should be overridden in concrete implementation, this is abstract class")

    @override
    def hwConfig(self):
        self._hwIOCls.hwConfig(self)

    @override
    def hwDeclr(self):
        addClkRstn(self)

        with self._hwParamsShared():
            self.bus = self._hwIOCls()

        self.decoded = HwIOStruct(
            self.STRUCT_TEMPLATE, tuple(),
            instantiateFieldFn=self._mkFieldInterface)._m()

    @staticmethod
    def HwIO_for_Bits(t):
        if t.const:
            t = copy(t)
            t.const = False
            p = HwIOSignal(dtype=t, masterDir=DIRECTION.IN)
        else:
            p = HwIORegCntrl()
        p.DATA_WIDTH = t.bit_length()
        return p

    def _mkFieldInterface(self, structHwIO: HwIOStruct, field: HStructField):
        """
        Instantiate field interface for fields in structure template of this endpoint

        :return: interface for specified field
        """
        t = field.dtype
        path = structHwIO._field_path / field.name
        shouldEnter, shouldUse = self.shouldEnterFn(self.STRUCT_TEMPLATE, path)

        if shouldUse:
            if isinstance(t, HBits):
                p = BusEndpoint.HwIO_for_Bits(t)
            elif isinstance(t, HArray):
                p = HwIOBramPort_noClk()
                assert isinstance(t.element_t, HBits), t.element_t
                p.DATA_WIDTH = t.element_t.bit_length()
                p.ADDR_WIDTH = log2ceil(t.size)
            else:
                raise NotImplementedError(t)

        elif shouldEnter:
            if isinstance(t, HArray):
                e_t = t.element_t
                if isinstance(e_t, HBits):
                    p = HObjList()
                    for i_i in range(int(t.size)):
                        i = BusEndpoint.HwIO_for_Bits(e_t)
                        structHwIO._fieldsToHwIOs[path / i_i] = i
                        p.append(i)
                elif isinstance(e_t, HStruct):
                    p = HObjList(
                        HwIOStruct(t.element_t,
                                   path / i,
                                   instantiateFieldFn=self._mkFieldInterface)
                        for i in range(int(t.size))
                    )
                    for i in p:
                        i._fieldsToHwIOs = structHwIO._fieldsToHwIOs
                else:
                    raise NotImplementedError()
            elif isinstance(t, HStruct):
                p = HwIOStruct(t, path,
                               instantiateFieldFn=self._mkFieldInterface)
                p._fieldsToHwIOs = structHwIO._fieldsToHwIOs
            else:
                raise TypeError(t)

        return p

    def getPort(self, transTmpl: TransTmpl):
        p = tuple(transTmpl.getFieldPath())
        return self.decoded._fieldsToHwIOs[p]

    def isInMyAddrRange(self, addr_sig):
        return inRange(addr_sig, self._ADDR_MIN, self._ADDR_MAX)

    def _parseTemplate(self):
        self.WORD_ADDR_STEP = self._getWordAddrStep()
        self.ADDR_STEP = self._getAddrStep()

        AW = int(self.ADDR_WIDTH)
        SUGGESTED_AW = self._suggestedAddrWidth()
        assert SUGGESTED_AW <= AW, ("Address width too small", SUGGESTED_AW, AW)
        tmpl = TransTmpl(self.STRUCT_TEMPLATE)

        self._ADDR_MIN = TransTmpl_get_min_addr(tmpl) // self.ADDR_STEP
        self._ADDR_MAX = ceil(TransTmpl_get_max_addr(tmpl) / self.ADDR_STEP)

        # resolve addresses for bram port mapped fields
        self._bramPortMapped = []

        def shouldEnterFn(trans_tmpl: TransTmpl):
            p = trans_tmpl.getFieldPath()
            hwIO = self.decoded._fieldsToHwIOs[p]
            if isinstance(hwIO, (HwIOStruct, HwIOUnionSink, HwIOUnionSource, HObjList)):
                shouldEnter = True
                shouldUse = False
            elif isinstance(hwIO, HwIOBramPort_noClk):
                shouldEnter = False
                shouldUse = True
            else:
                shouldEnter = False
                shouldUse = False

            return shouldEnter, shouldUse

        for ((base, end), t) in tmpl.HwIO_walkFlatten(shouldEnterFn=shouldEnterFn):
            self._bramPortMapped.append(((base, end), t))

        # resolve exact addresses for directly mapped field parts
        directly_mapped_fields = {}
        for p, out in self.decoded._fieldsToHwIOs.items():
            if not isinstance(out, (HwIORegCntrl, HwIOSignal)):
                continue
            a = directly_mapped_fields
            for _p in p:
                if isinstance(_p, int) and _p != 0:
                    # we need spec only for first array item
                    break
                a = a.setdefault(_p, {})

        dmw = self._directly_mapped_words = []
        if directly_mapped_fields:
            DW = self.DATA_WIDTH
            directly_mapped_t = HdlType_select(
                self.STRUCT_TEMPLATE,
                directly_mapped_fields)
            tmpl = TransTmpl(directly_mapped_t)

            frames = list(FrameTmpl.framesFromTransTmpl(
                tmpl, DW, maxPaddingWords=0,
                trimPaddingWordsOnStart=True,
                trimPaddingWordsOnEnd=True,))

            for f in frames:
                f_word_offset = f.startBitAddr // DW
                for (w_i, items) in f.walkWords(showPadding=True):
                    dmw.append((w_i + f_word_offset, items))

    def _suggestedAddrWidth(self):
        """
        Based on struct template resolve how many bits for
        address is needed
        """
        bitSize = self.STRUCT_TEMPLATE.bit_length()
        wordAddrStep = self._getWordAddrStep()
        addrStep = self._getAddrStep()

        # align to word size
        if bitSize % wordAddrStep != 0:
            bitSize += wordAddrStep - (bitSize % wordAddrStep)

        maxAddr = (bitSize // addrStep) - 1

        return maxAddr.bit_length()

    def propagateAddr(self, src_addr_sig: RtlSignal,
                      src_addr_step: int,
                      dst_addr_sig: RtlSignal,
                      dst_addr_step: int,
                      transTmpl: TransTmpl):
        """
        :param src_addr_sig: input signal with address
        :param src_addr_step: how many bits is addressing one unit of src_addr_sig
        :param dst_addr_sig: output signal for address
        :param dst_addr_step: how many bits is addressing one unit of dst_addr_sig
        :param transTmpl: TransTmpl which has meta-informations
            about this address space transition
        """
        IN_W = src_addr_sig._dtype.bit_length()

        # _prefix = transTmpl.getMyAddrPrefix(src_addr_step)
        assert dst_addr_step % src_addr_step == 0
        if not isinstance(transTmpl.dtype, HArray):
            raise TypeError(transTmpl.dtype)
        assert transTmpl.bitAddr % dst_addr_step == 0, (
            f"Has to be addressable by address with this step ({transTmpl})")

        addrIsAligned = transTmpl.bitAddr % transTmpl.bit_length() == 0 and isPow2(transTmpl.bit_length())
        bitsForAlignment = AddressStepTranslation(src_addr_step, dst_addr_step).align_bits
        bitsOfSubAddr = (
            (transTmpl.bitAddrEnd - transTmpl.bitAddr - 1)
            // dst_addr_step
        ).bit_length()

        if addrIsAligned:
            bitsOfAddr = bitsOfSubAddr + bitsForAlignment
            bitsOfPrefix = IN_W - bitsOfAddr
            prefix = (transTmpl.bitAddr // src_addr_step) >> bitsOfAddr
            if bitsOfPrefix == 0:
                addrIsInRange = True
            else:
                addrIsInRange = src_addr_sig[:(IN_W - bitsOfPrefix)]._eq(prefix)
            addr_tmp = src_addr_sig
        else:
            _addr = transTmpl.bitAddr // src_addr_step
            _addrEnd = transTmpl.bitAddrEnd // src_addr_step
            addrIsInRange = inRange(src_addr_sig, _addr, _addrEnd)
            addr_tmp = self._sig(dst_addr_sig._name +
                                 "_addr_tmp", HBits(self.ADDR_WIDTH))
            addr_tmp(src_addr_sig - _addr)

        if bitsOfSubAddr == 0:
            # :note: bitsOfSubAddr could be 0 if target array has 1 item
            assert dst_addr_sig._dtype.bit_length() == 1, dst_addr_sig._dtype
            connectedAddr = dst_addr_sig(0)
        else:
            addr_h = bitsOfSubAddr + bitsForAlignment
            connectedAddr = dst_addr_sig(
                addr_tmp[addr_h:bitsForAlignment]
            )

        return (addrIsInRange, connectedAddr)

    def connect_directly_mapped_read(self, ar_addr: RtlSignal,
                                     r_data: RtlSignal, default_r_data_drive):
        """
        Connect the HwIORegCntrl.din interfaces to a bus
        """
        DW = int(self.DATA_WIDTH)
        ADDR_STEP = self._getAddrStep()
        directlyMappedWords = []
        for (w_i, items) in self._directly_mapped_words:
            w_data = []
            last_end = w_i * DW
            for tpart in items:
                assert last_end == tpart.startOfPart, (last_end, tpart.startOfPart)
                if tpart.tmpl is None:
                    # padding
                    din = HBits(tpart.bit_length()).from_py(None)
                else:
                    din = self.getPort(tpart.tmpl)
                    if isinstance(din, HwIORegCntrl):
                        din = din.din
                if din._dtype.bit_length() > 1:
                    fr = tpart.getFieldBitRange()
                    din = din[fr[0]:fr[1]]
                w_data.append(din)
                last_end = tpart.endOfPart

            end_of_word = (w_i + 1) * DW
            assert last_end == end_of_word, (last_end, end_of_word)
            word_val = Concat(*reversed(w_data))
            assert word_val._dtype.bit_length() == DW, (items, word_val)
            directlyMappedWords.append((w_i * (DW // ADDR_STEP), word_val))

        mux = Switch(ar_addr).add_cases(
            [(word_i, r_data(val))
             for (word_i, val) in directlyMappedWords]
        )
        if default_r_data_drive:
            mux.Default(
                default_r_data_drive
            )
        return mux

    def connect_directly_mapped_write(self, aw_addr: RtlSignal,
                                      w_data: RtlSignal, en: RtlSignal):
        """
        Connect the HwIORegCntrl.dout interfaces to a bus
        """
        DW = int(self.DATA_WIDTH)
        addrWidth = int(self.ADDR_WIDTH)
        ADDR_STEP = self._getAddrStep()
        for w_i, items in self._directly_mapped_words:
            for tpart in items:
                if tpart.tmpl is None:
                    # padding
                    continue
                out = self.getPort(tpart.tmpl)
                if not isinstance(out, HwIORegCntrl):
                    continue
                else:
                    out = out.dout

                field_range = tpart.getFieldBitRange()
                if field_range != (out.DATA_WIDTH, 0):
                    raise NotImplementedError("Write on field not aligned to a word boundary", tpart)
                bus_range = tpart.getBusWordBitRange()
                out.data(w_data[bus_range[0]: bus_range[1]])
                addr = w_i * (DW // ADDR_STEP)
                out.vld(en & (aw_addr._eq(HBits(addrWidth).from_py(addr))))

    def connectByInterfaceMap(self, hwIOMap: HwIOObjMap):
        """
        Connect "decoded" struct interface to interfaces specified
        in interface map
        """
        assert isinstance(hwIOMap, HwIOObjMap), hwIOMap

        # connect interfaces as was specified by register map
        for convHwIO, hwIO in walkHwIOStructAndHwIOObjMap(self.decoded,
                                                       hwIOMap):
            if isinstance(hwIO, HwIOSignal):
                assert hwIO._direction == INTF_DIRECTION.MASTER
                if isinstance(convHwIO, HwIOSignal):
                    convHwIO(hwIO)
                else:
                    convHwIO.din(hwIO)

            elif isinstance(hwIO, RtlSignalBase):
                convHwIO.din(hwIO)

            elif isinstance(hwIO, HwIORegCntrl):
                assert hwIO._direction == INTF_DIRECTION.SLAVE
                hwIO(convHwIO)

            elif isinstance(hwIO, HwIODataVld):
                assert hwIO._direction == INTF_DIRECTION.SLAVE
                hwIO(convHwIO.dout)

            elif isinstance(hwIO, HwIOBramPort_noClk):
                hwIO(convHwIO)
            else:
                raise NotImplementedError(hwIO)

    @classmethod
    def fromHwIOMap(cls, interfaceMap):
        """
        Generate converter by struct data type specified by interface map

        :param interfaceMap: :func:`hwt.hwIOs.hwIO_map.HTypeFromHwIOObjMap`
        """
        t = HTypeFromHwIOObjMap(interfaceMap)

        def shouldEnter(root: HdlType, field_path: TypePath):
            actual = HwIOObjMap_get_by_field_path(interfaceMap, field_path)

            shouldEnter = isinstance(actual, (list, tuple, HStruct)) or (
                isinstance(actual, HStructField) and isinstance(actual.dtype, HStruct))
            shouldUse = not shouldEnter
            return shouldEnter, shouldUse

        # instantiate converter
        return cls(t, shouldEnterFn=shouldEnter)
