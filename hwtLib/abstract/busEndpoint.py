from copy import copy

from hwt.code import log2ceil
from hwt.hdlObjects.constants import INTF_DIRECTION
from hwt.hdlObjects.transTmpl import TransTmpl
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.array import Array
from hwt.hdlObjects.types.bits import Bits
from hwt.hdlObjects.types.hdlType import HdlType
from hwt.hdlObjects.types.struct import HStruct
from hwt.hdlObjects.types.structUtils import BusFieldInfo
from hwt.interfaces.std import BramPort_withoutClk, RegCntrl, Signal, VldSynced
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.interfaceLevel.interfaceUtils.proxy import InterfaceProxy
from hwt.synthesizer.interfaceLevel.mainBases import InterfaceBase
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.interfaceLevel.unitImplHelpers import getSignalName
from hwt.synthesizer.param import evalParam
from hwt.synthesizer.rtlLevel.mainBases import RtlSignalBase
from hwtLib.sim.abstractMemSpaceMaster import PartialField


def inRange(n, lower, end):
    return (n >= lower) & (n < end)


class BusEndpoint(Unit):
    """
    Abstract unit
    Delegate request from bus to fields of structure
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
        :param shouldEnterFn: function(transactionTemplate) which should return true if structuralized type like Array or HStruct
            should be interpreted as separate interfaces or not
        """
        assert intfCls is not None, "intfCls has to be specified"

        self._intfCls = intfCls
        self.STRUCT_TEMPLATE = structTemplate
        if shouldEnterFn is None:
            self.shouldEnterFn = lambda tmpl: not isinstance(tmpl.dtype, Array)
        else:
            self.shouldEnterFn = shouldEnterFn
        Unit.__init__(self)

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

    def walkFieldsAndIntf(self, transTmpl, structIntf):
        fieldTrans = transTmpl.walkFlatten(shouldEnterFn=self.shouldEnterFn)

        def shouldEnterIntf(intf):
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

        intfs = structIntf._walkFlatten(shouldEnterIntf)

        for (((base, end), transTmpl), intf) in zip(fieldTrans, intfs):
            if isinstance(intf, InterfaceProxy):
                _tTmpl = copy(transTmpl)
                _tTmpl.bitAddr = base
                _tTmpl.bitAddrEnd = end
                _tTmpl.origin = PartialField(transTmpl.origin)
                transTmpl = _tTmpl

            yield transTmpl, intf

    def _parseTemplate(self):
        self._directlyMapped = []
        self._bramPortMapped = []
        self.ADRESS_MAP = []

        self.WORD_ADDR_STEP = self._getWordAddrStep()
        self.ADDR_STEP = self._getAddrStep()

        def getIndexOfPart(transTmpl):
            index = 0
            parentArray = transTmpl.parent
            while not (isinstance(parentArray.dtype, Array) and parentArray.bitAddrEnd >= transTmpl.bitAddrEnd):
                parentArray = parentArray.parent
                if isinstance(parentArray.dtype, Array):
                    index += (transTmpl.bitAddr - parentArray.bitAddr) // parentArray.getItemWidth()
                    # [FIXME] not working correctly for multi level arrays
            return index

        AW = evalParam(self.ADDR_WIDTH).val
        SUGGESTED_AW = self._suggestedAddrWidth()
        assert SUGGESTED_AW <= AW, (SUGGESTED_AW, AW)
        tmpl = TransTmpl(self.STRUCT_TEMPLATE)
        # fieldTrans = tmpl.walkFlatten(shouldEnterFn=self.shouldEnterFn)

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
        lastItem = self.ADRESS_MAP[-1]
        return lastItem.bitAddrEnd // self._getAddrStep()

    def _getMinAddr(self):
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
        :param transTmpl: TransTmpl which has metainformations about this address space transition
        """
        IN_ADDR_WIDTH = srcAddrSig._dtype.bit_length()

        # _prefix = transTmpl.getMyAddrPrefix(srcAddrStep)
        assert dstAddrStep % srcAddrStep == 0
        if not isinstance(transTmpl.dtype, Array):
            raise TypeError()
        assert transTmpl.bitAddr % dstAddrStep == 0, "Has to be addressable by address with this step"

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
        t = field.dtype
        DW = evalParam(self.DATA_WIDTH).val

        if isinstance(t, Bits):
            p = RegCntrl()
            dw = t.bit_length()
        elif isinstance(t, Array):
            if self.shouldEnterFn(field):
                p = StructIntf(t.elmType, instantiateFieldFn=self._mkFieldInterface, asArraySize=t.size)
                return p
            else:
                p = BramPort_withoutClk()
                dw = t.elmType.bit_length()
                p.ADDR_WIDTH.set(log2ceil(evalParam(t.size).val - 1))
        else:
            raise NotImplementedError(t)

        if dw == DW:
            # use param instead of value to improve readability
            dw = self.DATA_WIDTH
            p._replaceParam("DATA_WIDTH", dw)
        else:
            p.DATA_WIDTH.set(dw)

        return p

    @classmethod
    def _resolveRegStructFromIntfMap(cls, prefix, interfaceMap, DATA_WIDTH, aliginFields=False):
        """
        Generate flattened register map for HStruct

        :param prefix: prefix for register name
        :param interfaceMap: iterable of
            tuple (type, name) or
            interface or
            tuple (list of interface, prefix, [aliginFields])
            (aliginFields is optional flag if set all items from list will be aligned to bus word size, default is false)
        :param DATA_WIDTH: width of word
        :return: generator of tuple (type, name, BusFieldInfo)
        """
        for m in interfaceMap:
            if isinstance(m, (InterfaceBase, RtlSignalBase)):
                intf = m
                name = getSignalName(intf)
                if isinstance(intf, (RtlSignalBase, Signal)):
                    dtype = intf._dtype
                    access = "r"
                elif isinstance(intf, VldSynced):
                    # assert intf._direction == INTF_DIRECTION.SLAVE
                    dtype = intf.data._dtype
                    access = "w"
                elif isinstance(intf, RegCntrl):
                    dtype = intf.din._dtype
                    access = "rw"
                elif isinstance(intf, BramPort_withoutClk):
                    dtype = Array(vecT(evalParam(intf.DATA_WIDTH).val),
                                  2 ** evalParam(intf.ADDR_WIDTH).val)
                    access = "rw"
                else:
                    raise NotImplementedError(intf)

                info = BusFieldInfo(access=access, fieldInterface=intf)

                if aliginFields:
                    fillUpWidth = DATA_WIDTH - dtype.bit_length()
                    if fillUpWidth > 0:
                        yield (vecT(fillUpWidth), None, None)

                yield (dtype, prefix + name, info)
            else:
                l = len(m)
                if l == 2:
                    typeOrListOfInterfaces, nameOrPrefix = m
                    align = False
                else:
                    typeOrListOfInterfaces, nameOrPrefix, align = m

                if isinstance(typeOrListOfInterfaces, HdlType):
                    # tuple (type, name)
                    yield (typeOrListOfInterfaces, prefix + nameOrPrefix, None)
                    if align:
                        fillUpWidth = DATA_WIDTH - typeOrListOfInterfaces.bit_length()
                        if fillUpWidth > 0:
                            yield (vecT(fillUpWidth), None, None)
                else:
                    # tuple (list of interfaces, prefix)
                    yield from cls._resolveRegStructFromIntfMap(prefix + nameOrPrefix,
                                                                typeOrListOfInterfaces,
                                                                DATA_WIDTH,
                                                                align)

    @classmethod
    def _fromInterfaceMap(cls, parent, onParentName, bus, busDataWidth, configFn, interfaceMap):
        """
        Generate converter by specified struct and connect interfaces if are specified
        in impl phase

        :param parent: unit where converter should be instantiated
        :param onParentName: name of converter in parent
        :param bus: bus interface for converter
        :param configFn: function (converter) which should be used for configuring of converter
        :param interfaceMap: iterable of tuple (type, name) or interface
            or tuple (list of interface, prefix, optionally align)
            (align is optional flag if set all items from list will be aligned (little-endian)
            to bus word size, default is false)
            if interface is specified it will be automatically connected
        """

        regsFlatten = []
        intfMap = {}
        DATA_WIDTH = evalParam(bus.DATA_WIDTH).val
        # build flatten register map
        for typ, name, info in cls._resolveRegStructFromIntfMap("", interfaceMap, DATA_WIDTH):
            if info is not None:
                regsFlatten.append((typ, name, info))
                intfMap[name] = info.fieldInterface
            else:
                regsFlatten.append((typ, name))

        # instantiate converter
        conv = cls(HStruct(*regsFlatten))
        configFn(conv)

        setattr(parent, onParentName, conv)

        conv.bus ** bus

        # connect interfaces as was specified by register map
        for regName, intf in intfMap.items():
            convIntf = getattr(conv.decoded, regName)

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
                convIntf.dout ** intf

            elif isinstance(intf, BramPort_withoutClk):
                intf ** convIntf
            else:
                raise NotImplementedError(intf)
