from copy import copy

from hwt.code import log2ceil
from hwt.hdlObjects.constants import INTF_DIRECTION
from hwt.hdlObjects.transTmpl import TransTmpl
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.array import Array
from hwt.hdlObjects.types.bits import Bits
from hwt.interfaces.std import BramPort_withoutClk, RegCntrl, Signal, VldSynced
from hwt.interfaces.structIntf import StructIntf, HTypeFromIntfMap
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.interfaceLevel.interfaceUtils.proxy import InterfaceProxy
from hwt.synthesizer.interfaceLevel.interfaceUtils.utils import walkFlatten
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.rtlLevel.mainBases import RtlSignalBase
from hwtLib.sim.abstractMemSpaceMaster import PartialField
from hwt.hdlObjects.types.hdlType import HdlType
from hwt.synthesizer.interfaceLevel.mainBases import InterfaceBase
from hwt.pyUtils.arrayQuery import where
from hwt.hdlObjects.types.struct import HStruct, HStructField


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


def walkStructIntfAndIntfMap(structIntf, intfMap):
    if isinstance(intfMap, (InterfaceBase, RtlSignalBase)):
        yield structIntf, intfMap
    elif isinstance(intfMap, tuple):
        try:
            item, name = intfMap
            if isinstance(item, HdlType):
                return
        except ValueError:
            name = None

        if isinstance(name, str):
            # is named something
            yield from walkStructIntfAndIntfMap(structIntf, item)
        else:
            # is struct described by tuple
            intfMap = list(where(intfMap, lambda x: not isPaddingInIntfMap(x)))
            assert len(intfMap) == len(structIntf._interfaces), (intfMap, structIntf)
            for sItem, item in zip(structIntf._interfaces, intfMap):
                yield from walkStructIntfAndIntfMap(sItem, item)

    else:
        if structIntf._isInterfaceArray():
            a = structIntf
        else:
            a = structIntf._interfaces

        assert len(a) == len(intfMap)
        for sItem, item in zip(a, intfMap):
            yield from walkStructIntfAndIntfMap(sItem, item)


class BusEndpoint(Unit):
    """
    Abstract unit
    Delegate request from bus to fields of structure
    (fields are represented by various interfaces)
    write has higher priority

    .. aafig::
        +------+    +----------+     +---------+
        | bus  +---->          +-----> field0  |
        |      <----+          <-----+         |
        +------+    |          |     +---------+
                    |          |
                    | endpoint |     +---------+
                    |          +-----> field1  |
                    |          <-----+         |
                    |          |     +---------+
                    |          |
                    |          |     +---------+
                    |          +-----> field2  |
                    |          <-----+         |
                    +----------+     +---------+

    """
    def __init__(self, structTemplate, intfCls=None, shouldEnterFn=None):
        """
        :param structTemplate: instance of HStruct which describes address space of this endpoint
        :param intfCls: class of bus interface which should be used
        :param shouldEnterFn: function(structField) return (shouldEnter, shouldUse)
            where shouldEnter is flag that means iterator over this interface
            should look inside of this actual object
            and shouldUse flag means that this field should be used (to create interface)
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
    def _defaultShouldEnterFn(field):
        t = field.dtype
        shouldEnter = isinstance(t, HStruct)
        shouldUse = not shouldEnter
        return shouldEnter, shouldUse

    def _getWordAddrStep(self):
        raise NotImplementedError("Should be overridden in concrete implementation, this is abstract class")

    def _getAddrStep(self):
        raise NotImplementedError("Should be overridden in concrete implementation, this is abstract class")

    def _config(self):
        self._intfCls._config(self)

    def _declr(self):
        addClkRstn(self)

        with self._paramsShared():
            self.bus = self._intfCls()

        self.decoded = StructIntf(self.STRUCT_TEMPLATE, instantiateFieldFn=self._mkFieldInterface)

    def getPort(self, transTmpl):
        o = transTmpl.origin
        return self.decoded._fieldsToInterfaces[o]

    def isInMyAddrRange(self, addrSig):
        return (addrSig >= self._getMinAddr()) & (addrSig < self._getMaxAddr())

    @staticmethod
    def _shouldEnterIntf(intf):
        """
        :return: tuple (shouldEnter, shouldYield)
        """
        if isinstance(intf, InterfaceProxy) and intf._itemsInOne == 1:
            if isinstance(intf._origIntf, (RegCntrl, BramPort_withoutClk)):
                return (False, True)
            else:
                return (True, False)
        if isinstance(intf, (RegCntrl, BramPort_withoutClk)):
            if intf._widthMultiplier is not None:
                return (False, False)
            else:
                return (False, True)
        else:
            return (True, False)

    def _shouldEnterForTransTmpl(self, tmpl):
        o = tmpl.origin

        if isinstance(o, HStructField):
            w = tmpl.bitAddrEnd - tmpl.bitAddr
            shouldEnter, shoulUse = self.shouldEnterFn(o)
            origW = tmpl.origin.dtype.bit_length()
            if not shoulUse and origW > w and isinstance(tmpl.dtype, Bits):
                return (False, True)
            else:
                return shouldEnter, shoulUse
        else:
            return (True, False)

    def walkFieldsAndIntf(self, transTmpl, structIntf):
        fieldTrans = transTmpl.walkFlatten(shouldEnterFn=self._shouldEnterForTransTmpl)
        intfs = walkFlatten(structIntf, self._shouldEnterIntf)

        hasAnyInterface = False
        for (((base, end), transTmpl), intf) in zip(fieldTrans, intfs):
            if isinstance(intf, InterfaceProxy):
                _tTmpl = copy(transTmpl)
                _tTmpl.bitAddr = base
                _tTmpl.bitAddrEnd = end
                _tTmpl.origin = PartialField(transTmpl.origin)
                transTmpl = _tTmpl

            yield transTmpl, intf
            hasAnyInterface = True

        assert hasAnyInterface

    def _parseTemplate(self):
        self._directlyMapped = []
        self._bramPortMapped = []
        self.ADRESS_MAP = []

        self.WORD_ADDR_STEP = self._getWordAddrStep()
        self.ADDR_STEP = self._getAddrStep()

        AW = int(self.ADDR_WIDTH)
        SUGGESTED_AW = self._suggestedAddrWidth()
        assert SUGGESTED_AW <= AW, (SUGGESTED_AW, AW)
        tmpl = TransTmpl(self.STRUCT_TEMPLATE)

        for transTmpl, intf in self.walkFieldsAndIntf(tmpl, self.decoded):
            if isinstance(intf, InterfaceProxy):
                self.decoded._fieldsToInterfaces[transTmpl.origin] = intf
                intfClass = intf._origIntf.__class__
            else:
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
        Based on strut template resolve how many bits for
        address is needed
        """
        bitSize = self.STRUCT_TEMPLATE.bit_length()
        wordAddrStep = self._getWordAddrStep()
        addrStep = self._getAddrStep()

        maxAddr = (bitSize // addrStep)

        # align to word size
        if maxAddr % wordAddrStep != 0:
            wordAddrStep += wordAddrStep - (maxAddr % wordAddrStep)

        return maxAddr.bit_length()

    def propagateAddr(self, srcAddrSig, srcAddrStep, dstAddrSig, dstAddrStep, transTmpl):
        """
        :param srcAddrSig: input signal with address
        :param srcAddrStep: how many bits is addressing one unit of srcAddrSig
        :param dstAddrSig: output signal for address
        :param dstAddrStep: how many bits is addressing one unit of dstAddrSig
        :param transTmpl: TransTmpl which has meta-informations about this address space transition
        """
        IN_ADDR_WIDTH = srcAddrSig._dtype.bit_length()

        # _prefix = transTmpl.getMyAddrPrefix(srcAddrStep)
        assert dstAddrStep % srcAddrStep == 0
        if not isinstance(transTmpl.dtype, Array):
            raise TypeError(transTmpl.dtype)
        assert transTmpl.bitAddr % dstAddrStep == 0, "Has to be addressable by address with this step (%r)" % (transTmpl)

        addrIsAligned = transTmpl.bitAddr % transTmpl.bit_length() == 0
        bitsForAlignment = ((dstAddrStep // srcAddrStep) - 1).bit_length()
        bitsOfSubAddr = ((transTmpl.bitAddrEnd - transTmpl.bitAddr - 1) // dstAddrStep).bit_length()

        if addrIsAligned:
            bitsOfPrefix = IN_ADDR_WIDTH - bitsOfSubAddr - bitsForAlignment
            prefix = (transTmpl.bitAddr // srcAddrStep) >> (bitsForAlignment + bitsOfSubAddr)
            addrIsInRange = srcAddrSig[IN_ADDR_WIDTH:(IN_ADDR_WIDTH - bitsOfPrefix)]._eq(prefix)
            addr_tmp = srcAddrSig
        else:
            _addr = transTmpl.bitAddr // srcAddrStep
            _addrEnd = transTmpl.bitAddrEnd // srcAddrStep
            addrIsInRange = inRange(srcAddrSig, _addr, _addrEnd)
            addr_tmp = self._sig(dstAddrSig._name + "_addr_tmp", vecT(self.ADDR_WIDTH))
            addr_tmp ** (srcAddrSig - _addr)

        connectedAddr = (dstAddrSig ** addr_tmp[(bitsOfSubAddr + bitsForAlignment):(bitsForAlignment)])

        return (addrIsInRange, connectedAddr)

    def _mkFieldInterface(self, structIntf, field):
        """
        Instantiate field interface for fields in structure template of this endpoint

        :return: interface for specified field
        """
        t = field.dtype
        DW = int(self.DATA_WIDTH)

        shouldEnter, shouldUse = self.shouldEnterFn(field)
        if shouldUse:
            if isinstance(t, Bits):
                p = RegCntrl()
                dw = t.bit_length()
            elif isinstance(t, Array):
                p = BramPort_withoutClk()
                assert isinstance(t.elmType, Bits)
                dw = t.elmType.bit_length()
                p.ADDR_WIDTH.set(log2ceil(t.size - 1))
            else:
                raise NotImplementedError(t)

        elif shouldEnter:
            if isinstance(t, Array):
                if isinstance(t.elmType, Bits):
                    p = RegCntrl(asArraySize=t.size)
                    dw = t.elmType.bit_length()
                else:
                    return StructIntf(t.elmType, instantiateFieldFn=self._mkFieldInterface, asArraySize=t.size)
            elif isinstance(t, HStruct):
                return StructIntf(t, instantiateFieldFn=self._mkFieldInterface)
            else:
                raise TypeError(t)

        if dw == DW:
            # use param instead of value to improve readability
            dw = self.DATA_WIDTH
            p._replaceParam("DATA_WIDTH", dw)
        else:
            p.DATA_WIDTH.set(dw)

        return p

    def connectByInterfaceMap(self, interfaceMap):
        """
        Connect "decoded" struct interface to interfaces specified
        in iterface map

        :param interfaceMap: list of interfaces or tuple (type or interface, name)
        """
        # connect interfaces as was specified by register map
        for convIntf, intf in walkStructIntfAndIntfMap(self.decoded, interfaceMap):
            if isinstance(intf, Signal):
                assert intf._direction == INTF_DIRECTION.MASTER
                convIntf.din ** intf

            elif isinstance(intf, RtlSignalBase):
                convIntf.din ** intf

            elif isinstance(intf, RegCntrl):
                assert intf._direction == INTF_DIRECTION.SLAVE
                intf ** convIntf

            elif isinstance(intf, VldSynced):
                assert intf._direction == INTF_DIRECTION.SLAVE
                intf ** convIntf.dout

            elif isinstance(intf, BramPort_withoutClk):
                intf ** convIntf
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

        def shouldEnter(field):
            if field.meta is None:
                shouldEnter = False
            else:
                shouldEnter = field.meta.split

            shouldYield = not shouldEnter
            return shouldEnter, shouldYield

        # instantiate converter
        return cls(t, shouldEnterFn=shouldEnter)
