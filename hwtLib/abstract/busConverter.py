from hwt.code import log2ceil
from hwt.hdlObjects.constants import INTF_DIRECTION
from hwt.hdlObjects.transactionTemplate import TransactionTemplate
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.array import Array
from hwt.hdlObjects.types.bits import Bits
from hwt.hdlObjects.types.hdlType import HdlType
from hwt.hdlObjects.types.struct import HStruct
from hwt.hdlObjects.types.structUtils import BusFieldInfo
from hwt.hdlObjects.types.typeCast import toHVal
from hwt.interfaces.std import BramPort_withoutClk, RegCntrl, Signal, VldSynced
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.interfaceLevel.mainBases import InterfaceBase
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.interfaceLevel.unitImplHelpers import getSignalName
from hwt.synthesizer.param import evalParam
from hwt.synthesizer.rtlLevel.mainBases import RtlSignalBase
from hwtLib.abstract.addrSpace import AddrSpaceItem


def inRange(n, lower, size):
    return (n >= lower) & (n < (toHVal(lower) + size))


class BusConverter(Unit):
    """
    Abstract unit
    Delegate request from bus to fields of structure
    write has higher priority

    :attention: interfaces are dynamically generated from names of fields in structure template
    """
    def __init__(self, structTemplate, offset=0, intfCls=None):
        """
        :param structTemplate:
            interface types for field type:
                primitive types like Bits -> RegCntrl interface
                Array -> BramPort_withoutClk interface
        """
        assert intfCls is not None, "intfCls has to be specified"
        self._intfCls = intfCls
        self.STRUCT_TEMPLATE = structTemplate
        self.OFFSET = offset
        Unit.__init__(self)

    def _getWordAddrStep(self):
        raise NotImplementedError("Should be overriden in concrete implementation, this is abstract class")

    def _getAddrStep(self):
        raise NotImplementedError("Should be overriden in concrete implementation, this is abstract class")

    def _config(self):
        self._intfCls._config(self)

    def _declr(self):
        addClkRstn(self)

        with self._paramsShared():
            self.bus = self._intfCls()

        self.decoded = StructIntf(self.STRUCT_TEMPLATE, instantiateFieldFn=self._mkFieldInterface)

    def constructAddrSpaceItemsForField(self):
        raise NotImplementedError()

    def _parseTemplate(self):
        self._directlyMapped = []
        self._bramPortMapped = []
        self.ADRESS_MAP = []

        self.WORD_ADDR_STEP = self._getWordAddrStep()
        self.ADDR_STEP = self._getAddrStep()

        AW = evalParam(self.ADDR_WIDTH).val
        DW = evalParam(self.DATA_WIDTH).val
        SUGGESTED_AW = self._suggestedAddrWidth()
        assert SUGGESTED_AW <= AW, (SUGGESTED_AW, AW)

        tmpl = TransactionTemplate(self.STRUCT_TEMPLATE, bitAddr=self.OFFSET*8)

        ADDR_STEP = self.WORD_ADDR_STEP
        OFFSETBITS_OF_WORDS = log2ceil(self._getWordAddrStep()).val
        for wIndx, tParts in tmpl.walkFrameWords():
            for tPart in tParts:
                if tPart.isPadding:
                    continue
                tItem = tPart.parent
                t = tItem.dtype

                assert len(tItem.parts) == 1

                if isinstance(t, Array):
                    size = evalParam(t.size).val
                    alignOffsetBits = OFFSETBITS_OF_WORDS
                else:
                    size = None
                    alignOffsetBits = None

                port = self.decoded._fieldsToInterfaces[tItem.origin]
                asi = AddrSpaceItem(wIndx * ADDR_STEP,
                                    tItem.name,
                                    size,
                                    origin=tItem.origin,
                                    alignOffsetBits=alignOffsetBits)

                asi.port = port
                if isinstance(port, RegCntrl):
                    self._directlyMapped.append(asi)
                elif isinstance(port, BramPort_withoutClk):
                    self._bramPortMapped.append(asi)
                else:
                    raise NotImplementedError(port)
                self.ADRESS_MAP.append(asi)

        # for field, intf in self.decoded._fieldsToInterfaces.items():

    def _getMaxAddr(self):
        lastItem = self.ADRESS_MAP[-1]
        if lastItem.size is None:
            return lastItem.addr
        else:
            return lastItem.addr + self.WORD_ADDR_STEP * lastItem.size

    def _getMinAddr(self):
        return self.ADRESS_MAP[0].addr

    def _suggestedAddrWidth(self):
        """
        Based on strut template and offset given resolve how many bits for
        address is needed
        """
        bitSize = self.STRUCT_TEMPLATE.bit_length()
        wordAddrStep = self.WORD_ADDR_STEP
        addrStep = self.ADDR_STEP

        maxAddr = (self.OFFSET + bitSize // addrStep)

        # align to word size
        if maxAddr % wordAddrStep != 0:
            wordAddrStep += wordAddrStep - (maxAddr % wordAddrStep)

        return maxAddr.bit_length()

    def _mkFieldInterface(self, field):
        t = field.dtype
        DW = evalParam(self.DATA_WIDTH).val

        if isinstance(t, Bits):
            p = RegCntrl()
            dw = t.bit_length()
        elif isinstance(t, Array):
            p = BramPort_withoutClk()
            dw = t.elmType.bit_length()
            p.ADDR_WIDTH.set(log2ceil(evalParam(t.size).val - 1))
        else:
            raise NotImplementedError(t)

        if dw == DW:
            # use param instead of value to improve readabiltiy
            dw = self.DATA_WIDTH
            p._replaceParam("DATA_WIDTH", dw)
        else:
            p.DATA_WIDTH.set(dw)

        return p

    @classmethod
    def _resolveRegStructFromIntfMap(cls, prefix, interfaceMap, DATA_WIDTH, aliginFields=False):
        """
        Generate flatened register map for HStruct

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
                    info = BusFieldInfo(access="r", fieldInterface=intf)
                elif isinstance(intf, VldSynced):
                    # assert intf._direction == INTF_DIRECTION.SLAVE
                    dtype = intf.data._dtype
                    info = BusFieldInfo(access="w", fieldInterface=intf)
                elif isinstance(intf, RegCntrl):
                    dtype = intf.din._dtype
                    info = BusFieldInfo(access="rw", fieldInterface=intf)
                elif isinstance(intf, BramPort_withoutClk):
                    dtype = Array(vecT(evalParam(intf.DATA_WIDTH).val),
                                  2 ** evalParam(intf.ADDR_WIDTH).val)
                    info = BusFieldInfo(access="rw", fieldInterface=intf)
                else:
                    raise NotImplementedError(intf)

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
            convIntf = getattr(conv, regName)

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
