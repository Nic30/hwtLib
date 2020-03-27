from copy import copy

from hwt.code import log2ceil
from hwt.hdl.constants import INTF_DIRECTION
from hwt.hdl.transTmpl import TransTmpl, ObjIteratorCtx
from hwt.hdl.types.array import HArray
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.hdlType import HdlType
from hwt.hdl.types.struct import HStruct, HStructField
from hwt.interfaces.std import BramPort_withoutClk, RegCntrl, Signal, VldSynced
from hwt.interfaces.structIntf import StructIntf, HTypeFromIntfMap, IntfMap
from hwt.interfaces.utils import addClkRstn
from hwt.pyUtils.arrayQuery import arr_any
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.interfaceLevel.mainBases import InterfaceBase
from hwt.synthesizer.interfaceLevel.unitImplHelpers import getSignalName
from hwt.synthesizer.rtlLevel.mainBases import RtlSignalBase
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwtLib.sim.abstractMemSpaceMaster import PartialField,\
    get_type_of_actual_field
from builtins import isinstance
from typing import Tuple, Union


def inRange(n, lower, end):
    return (n >= lower) & (n < end)


def isPaddingInIntfMap(item):
    if isinstance(item, HdlType):
        return True
    else:
        try:
            if isinstance(item, tuple):
                _item, name = item
                if name is None:
                    return True
        except ValueError:
            pass

    return False


def _walkStructIntfAndIntfMap_unpack(structIntf, intfMap):
    """
    Try to unpack intfMap and apply the selection on structIntf

    :return: Optional tuple Interface, intfMap
    """
    # items are Interface/RtlSignal or (type/interface/None or list of items, name)
    if isPaddingInIntfMap(intfMap):
        return
    elif isinstance(intfMap, tuple):
        item, name = intfMap
    else:
        item = intfMap
        assert isinstance(item, (InterfaceBase, RtlSignalBase)), item
        name = getSignalName(item)

    if isinstance(item, HdlType):
        # this part of structIntf was generated from type descriptin
        # and we are re searching only for those parts which were generated
        # from Interface/RtlSignal
        return

    return getattr(structIntf, name), item


def walkStructIntfAndIntfMap(structIntf, intfMap):
    """
    Walk StructInterfacece and interface map
    and yield tuples (Interface in StructInterface, interface in intfMap)
    which are on same place

    :param structIntf: HObjList or StructIntf or UnionIntf instance
    :param intfMap: interface map

    :note: typical usecase is when there is StructIntf generated from description in intfMap
        and then you need to connect interface from intfMap to structIntf
        and there you can use this function to iterate over interfaces which belongs together
    """

    if isinstance(intfMap, (InterfaceBase, RtlSignalBase)):
        yield structIntf, intfMap
        return
    elif isinstance(intfMap, tuple):
        item = _walkStructIntfAndIntfMap_unpack(structIntf, intfMap)
        if item is None:
            # is padding or there is no interface specified for it in intfMap
            return
        else:
            structIntf, item = item
            yield from walkStructIntfAndIntfMap(structIntf, item)
    elif isinstance(structIntf, list):
        structIntf
        assert len(structIntf) == len(intfMap)
        for sItem, item in zip(structIntf, intfMap):
            yield from walkStructIntfAndIntfMap(sItem, item)
    else:
        assert isinstance(intfMap, IntfMap), intfMap
        for item in intfMap:
            _item = _walkStructIntfAndIntfMap_unpack(structIntf, item)
            if _item is not None:
                sItem, _item = _item
                yield from walkStructIntfAndIntfMap(sItem, _item)


def get_shouldEnterForTransTmpl(shouldEnterFn_for_HdlType):
    def shouldEnterForTransTmpl(tmpl: TransTmpl):
        """
        This method drives the iterator over TransTmpl instance
        generated from input data type. It 
        """
        shouldEnter, shoulUse = shouldEnterFn_for_HdlType(tmpl.origin)
        return shouldEnter, shoulUse
    return shouldEnterForTransTmpl


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
        :param shouldEnterFn: function(structFieldPath) return (shouldEnter, shouldUse)
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
    def _defaultShouldEnterFn(field_path):
        """
        Default method which resolves how the parts of input data type
        should be represented on interface level.
        """
        t = get_type_of_actual_field(field_path)
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

    def getPort(self, transTmpl: TransTmpl):
        o = transTmpl.origin
        return self.decoded._fieldsToInterfaces[o]

    def isInMyAddrRange(self, addrSig):
        return (addrSig >= self._getMinAddr()) & (addrSig < self._getMaxAddr())

    def walkFieldsAndIntf(self, transTmpl, structIntf):
        intfIt = ObjIteratorCtx(structIntf)
        fieldTrans = transTmpl.walkFlatten(
            shouldEnterFn=get_shouldEnterForTransTmpl(self.shouldEnterFn),
            otherObjItCtx=intfIt)

        hasAnyInterface = False
        for ((base, end), transTmpl) in fieldTrans:
            intf = intfIt.actual
            isPartOfSomeArray = arr_any(intfIt.onParentNames,
                                        lambda x: isinstance(x, int))
            if isPartOfSomeArray:
                _tTmpl = copy(transTmpl)
                _tTmpl.bitAddr = base
                _tTmpl.bitAddrEnd = end
                _tTmpl.origin = (*transTmpl.origin[:-1], PartialField(transTmpl.origin))
                transTmpl = _tTmpl
                self.decoded._fieldsToInterfaces[transTmpl.origin] = intf

            yield transTmpl, intf
            hasAnyInterface = True

        assert hasAnyInterface, (transTmpl, structIntf)

    def _parseTemplate(self):
        self._directlyMapped = []
        self._bramPortMapped = []
        self.ADRESS_MAP = []

        self.WORD_ADDR_STEP = self._getWordAddrStep()
        self.ADDR_STEP = self._getAddrStep()

        AW = int(self.ADDR_WIDTH)
        SUGGESTED_AW = self._suggestedAddrWidth()
        assert SUGGESTED_AW <= AW, ("Address width too small", SUGGESTED_AW, AW)
        tmpl = TransTmpl(self.STRUCT_TEMPLATE)

        for transTmpl, intf in self.walkFieldsAndIntf(tmpl, self.decoded):
            intfClass = intf.__class__

            if issubclass(intfClass, RegCntrl):
                self._directlyMapped.append(transTmpl)

            elif issubclass(intfClass, BramPort_withoutClk):
                self._bramPortMapped.append(transTmpl)
            else:
                raise NotImplementedError(intf)

            self.ADRESS_MAP.append(transTmpl)

    def _getMaxAddr(self):
        """"
        Get maximum address value for this endpoint
        """
        lastItem = self.ADRESS_MAP[-1]
        return lastItem.bitAddrEnd // self._getAddrStep()

    def _getMinAddr(self):
        """"
        Get minimum address value for this endpoint
        """
        return self.ADRESS_MAP[0].bitAddr // self._getAddrStep()

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

    def propagateAddr(self, srcAddrSig: RtlSignal,
                      srcAddrStep: int,
                      dstAddrSig: RtlSignal,
                      dstAddrStep: int,
                      transTmpl: TransTmpl):
        """
        :param srcAddrSig: input signal with address
        :param srcAddrStep: how many bits is addressing one unit of srcAddrSig
        :param dstAddrSig: output signal for address
        :param dstAddrStep: how many bits is addressing one unit of dstAddrSig
        :param transTmpl: TransTmpl which has meta-informations
            about this address space transition
        """
        IN_ADDR_WIDTH = srcAddrSig._dtype.bit_length()

        # _prefix = transTmpl.getMyAddrPrefix(srcAddrStep)
        assert dstAddrStep % srcAddrStep == 0
        if not isinstance(transTmpl.dtype, HArray):
            raise TypeError(transTmpl.dtype)
        assert transTmpl.bitAddr % dstAddrStep == 0, (
            "Has to be addressable by address with this step (%r)" % (
                transTmpl))

        addrIsAligned = transTmpl.bitAddr % transTmpl.bit_length() == 0
        bitsForAlignment = ((dstAddrStep // srcAddrStep) - 1).bit_length()
        bitsOfSubAddr = (
            (transTmpl.bitAddrEnd - transTmpl.bitAddr - 1)
            // dstAddrStep
        ).bit_length()

        if addrIsAligned:
            bitsOfPrefix = IN_ADDR_WIDTH - bitsOfSubAddr - bitsForAlignment
            prefix = (transTmpl.bitAddr //
                      srcAddrStep) >> (bitsForAlignment + bitsOfSubAddr)
            if bitsOfPrefix == 0:
                addrIsInRange = True
            else:
                addrIsInRange = srcAddrSig[IN_ADDR_WIDTH:(
                    IN_ADDR_WIDTH - bitsOfPrefix)]._eq(prefix)
            addr_tmp = srcAddrSig
        else:
            _addr = transTmpl.bitAddr // srcAddrStep
            _addrEnd = transTmpl.bitAddrEnd // srcAddrStep
            addrIsInRange = inRange(srcAddrSig, _addr, _addrEnd)
            addr_tmp = self._sig(dstAddrSig._name + 
                                 "_addr_tmp", Bits(self.ADDR_WIDTH))
            addr_tmp(srcAddrSig - _addr)

        addr_h = bitsOfSubAddr + bitsForAlignment
        connectedAddr = dstAddrSig(
            addr_tmp[addr_h:bitsForAlignment]
        )

        return (addrIsInRange, connectedAddr)

    def _mkFieldInterface(self, structIntf: StructIntf, field):
        """
        Instantiate field interface for fields in structure template of this endpoint

        :return: interface for specified field
        """
        t = field.dtype
        dw = None
        path = (*structIntf._field_path, field)
        shouldEnter, shouldUse = self.shouldEnterFn(path)
        if shouldUse:
            if isinstance(t, Bits):
                p = RegCntrl()
                dw = t.bit_length()
            elif isinstance(t, HArray):
                p = BramPort_withoutClk()
                assert isinstance(t.element_t, Bits), t.element_t
                dw = t.element_t.bit_length()
                p.ADDR_WIDTH = log2ceil(t.size - 1)
            else:
                raise NotImplementedError(t)

        elif shouldEnter:
            if isinstance(t, HArray):
                e_t = t.element_t
                if isinstance(e_t, Bits):
                    p = HObjList(
                        RegCntrl() for _ in range(int(t.size))
                    )
                    dw = t.element_t.bit_length()
                elif isinstance(e_t, HStruct):
                    return HObjList(
                        StructIntf(t.element_t,
                                   (*path, i),
                                   instantiateFieldFn=self._mkFieldInterface)
                        for i in range(int(t.size))
                    )
                else:
                    raise NotImplementedError()
            elif isinstance(t, HStruct):
                return StructIntf(t, path,
                                  instantiateFieldFn=self._mkFieldInterface)
            else:
                raise TypeError(t)

        if isinstance(p, HObjList):
            _p = p
        else:
            _p = [p]

        if dw is not None:
            for i in _p:
                i.DATA_WIDTH = dw

        return p

    def connectByInterfaceMap(self, interfaceMap: IntfMap):
        """
        Connect "decoded" struct interface to interfaces specified
        in iterface map
        """
        assert isinstance(interfaceMap, IntfMap), interfaceMap

        # connect interfaces as was specified by register map
        for convIntf, intf in walkStructIntfAndIntfMap(self.decoded,
                                                       interfaceMap):
            if isinstance(intf, Signal):
                assert intf._direction == INTF_DIRECTION.MASTER
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
        Generate converter by specified struct

        :param interfaceMap: take a look at HTypeFromIntfMap
            if interface is specified it will be automatically connected
        """
        t = HTypeFromIntfMap(interfaceMap)

        def find_by_name(intf_map_item, name):
            assert isinstance(intf_map_item, IntfMap), intf_map_item
            for x in intf_map_item:
                if isinstance(x, InterfaceBase):
                    if x._name == name:
                        return x
                elif isinstance(x, RtlSignalBase):
                    if x.name == name:
                        return x
                else:
                    v, n = x
                    if n == name:
                        return v
            raise KeyError("Not in map", name)

        def shouldEnter(field_path):
            actual = interfaceMap
            # find in interfaceMap, skip first because it is the type itself
            for rec in field_path[1:]:
                if isinstance(rec, (InterfaceBase, RtlSignalBase)):
                    shouldEnter, shouldYield = False, True
                    return shouldEnter, shouldYield
                elif isinstance(rec, int):
                    actual = actual[rec]
                elif isinstance(rec, HStructField):
                    actual = find_by_name(actual, rec.name)
                else:
                    raise NotImplementedError(rec)

            shouldEnter = isinstance(actual, (list, tuple))
            shouldYield = not shouldEnter
            return shouldEnter, shouldYield

        # instantiate converter
        return cls(t, shouldEnterFn=shouldEnter)
