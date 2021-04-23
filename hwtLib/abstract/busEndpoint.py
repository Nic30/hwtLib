from builtins import isinstance
from copy import copy
from math import ceil
from typing import Union, Tuple

from hwt.code import Switch, Concat
from hwt.hdl.constants import INTF_DIRECTION
from hwt.hdl.frameTmpl import FrameTmpl
from hwt.hdl.transTmpl import TransTmpl
from hwt.hdl.types.array import HArray
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.hdlType import HdlType
from hwt.hdl.types.struct import HStruct, HStructField
from hwt.hdl.types.structUtils import field_path_get_type, HdlType_select
from hwt.interfaces.intf_map import IntfMap_get_by_field_path, IntfMap, \
    walkStructIntfAndIntfMap, HTypeFromIntfMap
from hwt.interfaces.std import BramPort_withoutClk, RegCntrl, Signal, VldSynced
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.unionIntf import UnionSink, UnionSource
from hwt.interfaces.utils import addClkRstn
from hwt.math import log2ceil, inRange, isPow2
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.rtlLevel.mainBases import RtlSignalBase
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.typePath import TypePath
from hwt.synthesizer.unit import Unit
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


class BusEndpoint(Unit):
    """
    Abstract unit

    Delegate request from bus to fields of structure
    (fields are represented by various interfaces)
    write has higher priority

    :note: implementation is usually address decoder

    .. aafig::

        +------+    +----------+     +---------+
        | bus  +--->|          +---->| field0  |
        |      |<---+          |<----+         |
        +------+    |          |     +---------+
                    |          |
                    | endpoint |     +---------+
                    |          +---->| field1  |
                    |          |<----+         |
                    |          |     +---------+
                    |          |
                    |          |     +---------+
                    |          +---->| field2  |
                    |          |<----+         |
                    +----------+     +---------+

    """

    def __init__(self, structTemplate, intfCls=None, shouldEnterFn=None):
        """
        :param structTemplate: instance of HStruct which describes
            address space of this endpoint
        :param intfCls: class of bus interface which should be used
        :param shouldEnterFn: function(root_t, structFieldPath) return (shouldEnter, shouldUse)
            where shouldEnter is flag that means iterator over this interface
            should look inside of this actual object
            and shouldUse flag means that this field should be used
            (to create interface)
        """
        assert intfCls is not None, "intfCls has to be specified"

        self._intfCls = intfCls
        self.STRUCT_TEMPLATE = structTemplate
        if shouldEnterFn is None:
            self.shouldEnterFn = self._defaultShouldEnterFn
        else:
            self.shouldEnterFn = shouldEnterFn
        Unit.__init__(self)

    @staticmethod
    def _defaultShouldEnterFn(root: HdlType, field_path: Tuple[Union[str, int]]):
        """
        Default method which resolves how the parts of input data type
        should be represented on interface level.
        """
        t = field_path_get_type(root, field_path)
        isNonPrimitiveArray = isinstance(t, HArray) and\
            not isinstance(t.element_t, Bits)
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

    def _config(self):
        self._intfCls._config(self)

    def _declr(self):
        addClkRstn(self)

        with self._paramsShared():
            self.bus = self._intfCls()

        self.decoded = StructIntf(
            self.STRUCT_TEMPLATE, tuple(),
            instantiateFieldFn=self._mkFieldInterface)._m()

    @staticmethod
    def intf_for_Bits(t):
        if t.const:
            t = copy(t)
            t.const = False
            p = Signal(dtype=t, masterDir=DIRECTION.IN)
        else:
            p = RegCntrl()
        p.DATA_WIDTH = t.bit_length()
        return p

    def _mkFieldInterface(self, structIntf: StructIntf, field: HStructField):
        """
        Instantiate field interface for fields in structure template of this endpoint

        :return: interface for specified field
        """
        t = field.dtype
        path = structIntf._field_path / field.name
        shouldEnter, shouldUse = self.shouldEnterFn(self.STRUCT_TEMPLATE, path)

        if shouldUse:
            if isinstance(t, Bits):
                p = BusEndpoint.intf_for_Bits(t)
            elif isinstance(t, HArray):
                p = BramPort_withoutClk()
                assert isinstance(t.element_t, Bits), t.element_t
                p.DATA_WIDTH = t.element_t.bit_length()
                p.ADDR_WIDTH = log2ceil(t.size)
            else:
                raise NotImplementedError(t)

        elif shouldEnter:
            if isinstance(t, HArray):
                e_t = t.element_t
                if isinstance(e_t, Bits):
                    p = HObjList()
                    for i_i in range(int(t.size)):
                        i = BusEndpoint.intf_for_Bits(e_t)
                        structIntf._fieldsToInterfaces[path / i_i] = i
                        p.append(i)
                elif isinstance(e_t, HStruct):
                    p = HObjList(
                        StructIntf(t.element_t,
                                   path / i,
                                   instantiateFieldFn=self._mkFieldInterface)
                        for i in range(int(t.size))
                    )
                    for i in p:
                        i._fieldsToInterfaces = structIntf._fieldsToInterfaces
                else:
                    raise NotImplementedError()
            elif isinstance(t, HStruct):
                p = StructIntf(t, path,
                               instantiateFieldFn=self._mkFieldInterface)
                p._fieldsToInterfaces = structIntf._fieldsToInterfaces
            else:
                raise TypeError(t)

        return p

    def getPort(self, transTmpl: TransTmpl):
        p = tuple(transTmpl.getFieldPath())
        return self.decoded._fieldsToInterfaces[p]

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
            intf = self.decoded._fieldsToInterfaces[p]
            if isinstance(intf, (StructIntf, UnionSink, UnionSource, HObjList)):
                shouldEnter = True
                shouldUse = False
            elif isinstance(intf, BramPort_withoutClk):
                shouldEnter = False
                shouldUse = True
            else:
                shouldEnter = False
                shouldUse = False

            return shouldEnter, shouldUse

        for ((base, end), t) in tmpl.walkFlatten(shouldEnterFn=shouldEnterFn):
            self._bramPortMapped.append(((base, end), t))

        # resolve exact addresses for directly mapped field parts
        directly_mapped_fields = {}
        for p, out in self.decoded._fieldsToInterfaces.items():
            if not isinstance(out, (RegCntrl, Signal)):
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
                                 "_addr_tmp", Bits(self.ADDR_WIDTH))
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
        Connect the RegCntrl.din interfaces to a bus
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
                    din = Bits(tpart.bit_length()).from_py(None)
                else:
                    din = self.getPort(tpart.tmpl)
                    if isinstance(din, RegCntrl):
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
        Connect the RegCntrl.dout interfaces to a bus
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
                if not isinstance(out, RegCntrl):
                    continue
                else:
                    out = out.dout

                field_range = tpart.getFieldBitRange()
                if field_range != (out.DATA_WIDTH, 0):
                    raise NotImplementedError("Write on field not aligned to a word boundary", tpart)
                bus_range = tpart.getBusWordBitRange()
                out.data(w_data[bus_range[0]: bus_range[1]])
                addr = w_i * (DW // ADDR_STEP)
                out.vld(en & (aw_addr._eq(Bits(addrWidth).from_py(addr))))

    def connectByInterfaceMap(self, interfaceMap: IntfMap):
        """
        Connect "decoded" struct interface to interfaces specified
        in interface map
        """
        assert isinstance(interfaceMap, IntfMap), interfaceMap

        # connect interfaces as was specified by register map
        for convIntf, intf in walkStructIntfAndIntfMap(self.decoded,
                                                       interfaceMap):
            if isinstance(intf, Signal):
                assert intf._direction == INTF_DIRECTION.MASTER
                if isinstance(convIntf, Signal):
                    convIntf(intf)
                else:
                    convIntf.din(intf)

            elif isinstance(intf, RtlSignalBase):
                convIntf.din(intf)

            elif isinstance(intf, RegCntrl):
                assert intf._direction == INTF_DIRECTION.SLAVE
                intf(convIntf)

            elif isinstance(intf, VldSynced):
                assert intf._direction == INTF_DIRECTION.SLAVE
                intf(convIntf.dout)

            elif isinstance(intf, BramPort_withoutClk):
                intf(convIntf)
            else:
                raise NotImplementedError(intf)

    @classmethod
    def fromInterfaceMap(cls, interfaceMap):
        """
        Generate converter by struct data type specified by interface map

        :param interfaceMap: :func:`hwt.interfaces.intf_map.HTypeFromIntfMap`
        """
        t = HTypeFromIntfMap(interfaceMap)

        def shouldEnter(root: HdlType, field_path: TypePath):
            actual = IntfMap_get_by_field_path(interfaceMap, field_path)

            shouldEnter = isinstance(actual, (list, tuple, HStruct)) or (
                isinstance(actual, HStructField) and isinstance(actual.dtype, HStruct))
            shouldUse = not shouldEnter
            return shouldEnter, shouldUse

        # instantiate converter
        return cls(t, shouldEnterFn=shouldEnter)
