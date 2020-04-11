from copy import copy
import json
from math import ceil
from typing import List, Tuple

from hwt.code import If
from hwt.code_utils import rename_signal
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.intf_map import IntfMap, HTypeFromIntfMap
from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.unit import Unit


class MonitorOf(Interface):
    """
    Interfaces same as template interface, but with all signals as an input
    """

    def __init__(self, template_interface):
        self.__template_interface = template_interface
        super(MonitorOf, self).__init__()

    def _config(self):
        """
        Copy config from template interface
        """
        tmpl = self.__template_interface
        for p in tmpl._params:
            setattr(self, p._name, p.get_value())

    def _declr(self):
        """
        Create interfaces same as on template interface, but make them always input
        """
        tmpl = self.__template_interface
        for i in tmpl._interfaces:
            setattr(self, i._name, monitor_of(i))


def monitor_of(intf: Interface):
    if intf._interfaces:
        return MonitorOf(intf)
    else:
        if not isinstance(intf, Signal):
            raise NotImplementedError()
        return Signal(dtype=intf._dtype)


def interface_to_HdlType(intf: Interface, const=False):
    if intf._interfaces:
        return HStruct(
            *((interface_to_HdlType(i, const=const), i._name)
              for i in intf._interfaces)
        )
    else:
        t = intf._dtype
        if t.const != const:
            t = copy(t)
            t.const = const
        return t


def connect_MonitorOf(dst, src: MonitorOf):
    """
    Connect signal by signal and ignore the directions of struct interface
    (check only direction of low level signals)
    """
    if src._interfaces:
        for _src in src._interfaces:
            _dst = getattr(dst, _src._name)
            connect_MonitorOf(_dst, _src)
    else:
        src = src._reinterpret_cast(dst._dtype)
        dst(src)

def connect_to_MonitorOf(dst: MonitorOf, src):
    """
    Connect signal by signal and ignore the directions of struct interface
    (check only direction of low level signals)
    """
    if dst._interfaces:
        for _dst in dst._interfaces:
            _src = getattr(src, _dst._name)
            connect_to_MonitorOf(_dst, _src)
    else:
        dst(src)


class DebugBusMonitor(Unit):
    """
    This component is similar to ILA/ChipScope/SignalTAP
    but it is not connected to internal JTAG, but to a specified interface.
    This component generates an address decoder and connect all specified
    interfaces to a service bus. It also stores the names and bit widths
    of original interfaces in a ROM in order to display them later
    in test application. This component also supports for snapshots
    of values by a generic trigger method, transaction counters etc.

    :note: addressspace size depends on how much data is actually monitored.
        But it has fixed structure.

    .. code-block: c

        struct address_space {
            // value 0 means the name memory is explicitly dissabled
            uint32_t name_memory_size;
            uint32_t name_memory_offset; // offsetof(address_space, data)
            // n can be resolved from content of name_memory
            // as well as structure of data_memory
            uint8_t data_memory[n];
            // padding to size 2**x
            char name_memory[name_memory_size]; // contains a JSON with data info
        };

    Example of name_memory JSON format:

    .. code-block: javascript

        {
            "p0": {
               "c0": [0, 16], // signal p0.c0 is stored in data_memory[0:2]
               "c1": [16, 16], // signal p0.c0 is stored in data_memory[2:4]
            },
            "p1": [32, 1], //signal p1 is stored in data_memory[5] bit 0
            "p2": [33, 1], //signal p1 is stored in data_memory[5] bit 1
        }

    """

    def __init__(self, bus_cls, bus_endpoint_cls):
        self._bus_cls = bus_cls
        self._bus_endpoint_cls = bus_endpoint_cls
        self.io_instanciated = False
        super(DebugBusMonitor, self).__init__()

    def _config(self):
        self._bus_cls._config(self)
        self.monitored_data = []

    def register(self, intf: Interface, name=None):
        assert not self.io_instanciated
        if name is None:
            name = intf._getPhysicalName()
        self.monitored_data.append((intf, name))

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.s = self._bus_cls()
        self.monitor = HObjList([
            monitor_of(intf) for (intf, _) in self.monitored_data
        ])
        self.io_instanciated = True

        # declare an interface with same signalls but all inputs for each monitored interface
    def _impl(self):
        name_memory, name_memory_size = self.build_name_memory(self.monitored_data)
        const_uint32_t = Bits(32, signed=False, const=True)
        addr_space = IntfMap([
            (const_uint32_t, "name_memory_size"),
            (const_uint32_t, "name_memory_offset"),
            (IntfMap(
                (interface_to_HdlType(i, const=True), name)
                for i, name in self.monitored_data
            ), "data_memory"),
        ])
        data_part_t = HTypeFromIntfMap(addr_space)
        data_part_width = data_part_t.bit_length()
        closest_pow2 = 2**data_part_width.bit_length()
        if data_part_width != closest_pow2:
            # padding between data_memory and name_memory
            addr_space.append((Bits(closest_pow2 - data_part_width), None))    
        name_memory_offset = closest_pow2 // 8

        addr_space.append(
            (Bits(self.DATA_WIDTH, const=True)[name_memory_size // (self.DATA_WIDTH // 8)], "name_memory")
        )
        
        ep = self._bus_endpoint_cls.fromInterfaceMap(addr_space)

        with self._paramsShared():
            self.ep = ep
        ep.bus(self.s)

        ep.decoded.name_memory_size(name_memory_size)
        ep.decoded.name_memory_offset(name_memory_offset)
        for intf, (_, name) in zip(self.monitor, self.monitored_data):
            to_bus_intf = getattr(ep.decoded.data_memory, name)
            connect_MonitorOf(to_bus_intf, intf)

        name_memory = rename_signal(self, name_memory, "name_memory")
        name_memory_reader = ep.decoded.name_memory
        If(self.clk._onRisingEdge(),
            If(name_memory_reader.en,
               name_memory_reader.dout(name_memory[name_memory_reader.addr])
            )
        )

        propagateClkRstn(self)
    
    @classmethod
    def _build_name_memory(cls, intf: Interface, offset: int):
        if intf._interfaces:
            res = {}
            for i in intf._interfaces:
                offset, _i = cls._build_name_memory(i, offset)
                res[i._name] = _i
            return offset, res
        else:
            w = intf._dtype.bit_length()
            return offset + w, [offset, w]
        return offset

    def build_name_memory(self, monitored_data: List[Tuple[Interface, str]]):
        res = {}
        offset = 0
        for i, name in monitored_data:
            offset, _i = self._build_name_memory(i, offset)
            res[name] = _i
        res = json.dumps(res).encode("utf-8")
        DW = self.DATA_WIDTH
        nam_data_width = ceil(((len(res) + 1) * 8) / DW) * DW
        res = Bits(nam_data_width).from_py(int.from_bytes(res, "little"))
        res = res._reinterpret_cast(Bits(DW)[nam_data_width//DW])
        return res, nam_data_width // 8

    def apply_connections(self):
        """
        Connect a monitored interface to monitor ports of this component
        """
        for intf, (orig_intf, _) in zip(self.monitor, self.monitored_data):
            connect_to_MonitorOf(intf, orig_intf)
