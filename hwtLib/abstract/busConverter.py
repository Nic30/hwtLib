from hwt.code import log2ceil, connect
from hwt.hdlObjects.constants import INTF_DIRECTION
from hwt.hdlObjects.types.typeCast import toHVal
from hwt.interfaces.std import BramPort_withoutClk, RegCntrl, Signal, VldSynced
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import evalParam
from hwtLib.abstract.addrSpace import AddrSpaceItem


def unpackAddrMap(am):
    if isinstance(am, AddrSpaceItem):
        return am
    try:
        size = am[2]
    except IndexError:
        size = None

    # address, name, size
    return AddrSpaceItem(am[0], am[1], size)


class BusConverter(Unit):
    def __init__(self, adress_map):
        """
        @param address_map: array of tupes (address, name) or (address, name, size)
                            where size is in data words or AddrSpaceItem objects

                    for every tuple without size there will be RegCntrl interface
                    for every tuble with size there will be blockram port without clk
        """
        self.ADRESS_MAP = list(sorted(map(unpackAddrMap, adress_map), key=lambda x: x.addr))
        super().__init__()

    def getMinAddr(self):
        return self.ADRESS_MAP[0].addr

    def getMaxAddr(self):
        m = self.ADRESS_MAP[-1]
        if m.size is not None:
            if m.alignOffsetBits:
                size = evalParam(m.size).val << m.alignOffsetBits
            else:
                size = m.size
            return toHVal(m.addr) + (size - 1)
        else:
            return toHVal(m.addr)

    def suggestedAddrWidth(self):
        maxAddr = evalParam(self.getMaxAddr()).val
        return maxAddr.bit_length()

    def decorateWithConvertedInterfaces(self):
        assert len(self.ADRESS_MAP) > 0

        self._directlyMapped = []
        self._bramPortMapped = []
        self._addrSpace = []

        for am in self.ADRESS_MAP:
            addrItem = unpackAddrMap(am)
            if addrItem.size is None:
                addrItem.size = 1
                p = RegCntrl()
                p._replaceParam("DATA_WIDTH", self.DATA_WIDTH)
                self._directlyMapped.append(addrItem)
            else:
                p = BramPort_withoutClk()
                p._replaceParam("DATA_WIDTH", self.DATA_WIDTH)
                p.ADDR_WIDTH.set(log2ceil(addrItem.size - 1))
                self._bramPortMapped.append(addrItem)

            self._addrSpace.append(addrItem)
            addrItem.port = p
            p._addrSpaceItem = addrItem

            setattr(self, addrItem.name, p)

    @classmethod
    def _resolveRegFiles(cls, prefix, addrStep, regs):
        """
        generator of tuple ( (addr, name), interface ) where interface is None when register is specified by name instead of interface
        @param regs: iterable of tuples
                 (addr, name) or
                 (addr, name, interfaces)

                 if addr is None addr is uatomaticaly generated by addrStep
        @param addrStep: step in addr between registers
        @param prefix: prefix for register name
        """
        lastAddr = 0x0
        for reg in regs:
            if len(reg) == 3 and isinstance(reg[2], (list, tuple)):
                addr, name, interfaces = reg

                if addr is None:
                    lastAddr += addrStep
                    addr = lastAddr

                for i, intf in enumerate(interfaces):
                    # we expect all to be specified by interface because there
                    # should not be any any register without connection in subunits
                    fieldAddr = addr + i * addrStep
                    yield (fieldAddr, prefix + name + intf._name), intf
                    lastAddr += addrStep

            else:
                addr, name = reg
                if addr is None:
                    lastAddr += addrStep
                    addr = lastAddr
                else:
                    lastAddr = addr

                yield (addr, prefix + name), None

    @classmethod
    def _buildForAddrSpace(cls, parent, onParentName, bus, busDataWidth, configFn, addrSpace):
        regsFlatten = []
        intfMap = {}
        # build flatten register map
        for reg, intf in cls._resolveRegFiles("", evalParam(busDataWidth).val // 8, addrSpace):
            regsFlatten.append(reg)
            if intf is not None:
                _, name = reg
                intfMap[name] = intf

        # instantiate converter
        conv = cls(regsFlatten)
        configFn(conv)

        setattr(parent, onParentName, conv)

        conv.bus ** bus

        # connect interfaces as was specified by register map
        for regName, intf in intfMap.items():
            convIntf = getattr(conv, regName)

            if isinstance(intf, Signal):
                assert intf._direction == INTF_DIRECTION.MASTER
                connect(intf, convIntf.din, fit=True)

            elif isinstance(intf, RegCntrl):
                assert intf._direction == INTF_DIRECTION.SLAVE
                connect(convIntf, intf, fit=True)

            elif isinstance(intf, VldSynced):
                assert intf._direction == INTF_DIRECTION.SLAVE
                connect(convIntf.dout, intf, fit=True)

            else:
                raise NotImplementedError()
