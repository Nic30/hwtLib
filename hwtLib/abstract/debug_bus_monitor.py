from copy import copy
import json
from math import ceil
from typing import List, Tuple, Optional, Type, Union

from hwt.code import If
from hwt.code_utils import rename_signal
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.struct import HStruct
from hwt.hdl.types.structValBase import StructValBase
from hwt.interfaces.intf_map import IntfMap, HTypeFromIntfMap
from hwt.interfaces.std import Signal, VldSynced
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.interfaceLevel.mainBases import InterfaceBase
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.mainBases import RtlSignalBase
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwtLib.clocking.vldSynced_cdc import VldSyncedCdc
from hwt.interfaces.structIntf import Interface_to_HdlType


class MonitorIntf(Interface):
    """
    Interfaces same as template interface, but with all signals as an input
    """

    def __init__(self, template_interface):
        self._template_interface = template_interface
        super(MonitorIntf, self).__init__()

    @staticmethod
    def _bound_intf(template_interface, cls=None):
        if cls is None:
            cls = MonitorIntf

        class BoundedMonitorIntf(cls):
            def __init__(self):
                super(BoundedMonitorIntf, self).__init__(template_interface)
        return BoundedMonitorIntf

    def _config(self):
        """
        Copy config from template interface
        """
        tmpl = self._template_interface
        for p in tmpl._params:
            setattr(self, p._name, p.get_value())

    def _declr(self):
        """
        Create interfaces same as on template interface,
        but make them always input
        """
        tmpl = self._template_interface
        for i in tmpl._interfaces:
            setattr(self, i._name, monitor_of(i))


class MonitorIntfVldSynced(VldSynced):

    def __init__(self, template_interface):
        self._template_interface = template_interface
        super(MonitorIntfVldSynced, self).__init__()

    def _config(self):
        MonitorIntf._config(self)

    def _declr(self):
        self.data = MonitorIntf(self._template_interface)
        self.vld = Signal()


class MonitorIntfVldSyncedCdc(VldSyncedCdc):

    def __init__(self, template_interface):
        """
        :param template_interface: an Interface instance which will be monitored,
            used as template for this interface
        """
        intf_cls = MonitorIntf._bound_intf(
            template_interface, cls=MonitorIntfVldSynced)
        self._template_interface = template_interface
        super(MonitorIntfVldSyncedCdc, self).__init__(intf_cls)


def monitor_of(intf: Union[Interface, RtlSignal]):
    """
    Create a monitor interface for specified interface
    (monitor interface is an interface which reads all signals of choosen interface)
    """
    if isinstance(intf, Interface) and intf._interfaces:
        return MonitorIntf(intf)
    else:
        if not isinstance(intf, (Signal, RtlSignalBase)):
            raise NotImplementedError(intf)
        return Signal(dtype=intf._dtype)


def _connect_MonitorIntf(src: MonitorIntf, dst):
    if src._interfaces:
        for _src in src._interfaces:
            _dst = getattr(dst, _src._name)
            yield from _connect_MonitorIntf(_src, _dst)
    else:
        src = src._reinterpret_cast(dst._dtype)
        yield dst(src)


def connect_MonitorIntf(src: MonitorIntf, dst):
    """
    Connect signal by signal and ignore the directions of struct interface
    (check only direction of low level signals)
    """
    return list(_connect_MonitorIntf(src, dst))


def _connect_to_MonitorIntf(src, dst: MonitorIntf):
    if isinstance(dst, (StructValBase, RtlSignal)):
        if src._interfaces:
            for _src in src._interfaces:
                _dst = getattr(dst, _src._name)
                yield from _connect_to_MonitorIntf(_src, _dst)
            return
    else:
        if dst._interfaces:
            for _dst in dst._interfaces:
                _src = getattr(src, _dst._name)
                yield from _connect_to_MonitorIntf(_src, _dst)
            return
    yield dst(src)


def connect_to_MonitorIntf(src, dst: MonitorIntf):
    """
    Connect signal by signal and ignore the directions of struct interface
    (check only direction of low level signals)
    """
    return list(_connect_to_MonitorIntf(src, dst))


class MonitorIntfReg(Unit):
    def __init__(self, intfCls: Type[MonitorIntf]):
        self.intfCls = intfCls
        Unit.__init__(self)

    def _config(self):
        Unit._config(self)


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
        self.io_instantiated = False
        super(DebugBusMonitor, self).__init__()

    def _config(self):
        self._bus_cls._config(self)
        self.monitored_data = []
        self.ADD_NAME_MEMORY = Param(True)

    def register(self, intf: Interface,
                 name: Optional[str]=None,
                 cdc: bool=False,
                 trigger: Optional[RtlSignal]=None,
                 add_reg: bool=False):
        """
        :param intf: an interface to monitor
        :param name: name override
        :param cdc: if True instantiate Clock domain crossing to synchronize input
            data to clock domain of this component
        :param trigger: an optional signal which triggers the snapshot of this interface
        :note: if cdc is set to True the trigger has to be synchonezed to a clock clock domain of intf
        :param add_reg: if True an register is added between input and bus interface
        """
        assert not self.io_instantiated
        if name is None:
            if isinstance(intf, InterfaceBase):
                name = intf._getHdlName()
            else:
                name = intf.name
        self.monitored_data.append((intf, name, cdc, trigger, add_reg))

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.s = self._bus_cls()
        # declare an interface with same signals but all inputs for each
        # monitored interface
        self.monitor = HObjList([
            monitor_of(intf) for (intf, _, _, _, _) in self.monitored_data
        ])
        self.io_instantiated = True

    def _impl(self):
        if self.ADD_NAME_MEMORY:
            name_memory, name_memory_size, name_content_size =\
                self.build_name_memory(self.monitored_data)
        else:
            name_content_size = 0
        const_uint32_t = Bits(32, signed=False, const=True)
        addr_space = IntfMap([
            (const_uint32_t, "name_memory_size"),
            (const_uint32_t, "name_memory_offset"),
            (IntfMap(
                (Interface_to_HdlType().apply(i, const=True), name)
                for i, name, _, _, _ in self.monitored_data
            ), "data_memory"),
        ])
        data_part_t = HTypeFromIntfMap(addr_space)
        data_part_width = data_part_t.bit_length()
        if self.ADD_NAME_MEMORY:
            closest_pow2 = 2**data_part_width.bit_length()
            if data_part_width != closest_pow2:
                # padding between data_memory and name_memory
                addr_space.append((Bits(closest_pow2 - data_part_width), None))
            name_memory_offset = closest_pow2 // 8

            name_mem_words = name_memory_size // (self.DATA_WIDTH // 8)
            addr_space.append(
                (Bits(self.DATA_WIDTH, const=True)[name_mem_words],
                 "name_memory")
            )
        else:
            name_memory_offset = 0

        ep = self._bus_endpoint_cls.fromInterfaceMap(addr_space)

        with self._paramsShared():
            self.ep = ep
        ep.bus(self.s)

        ep.decoded.name_memory_size(name_content_size)
        ep.decoded.name_memory_offset(name_memory_offset)
        for intf, (_, name, _, _, _) in zip(self.monitor, self.monitored_data):
            to_bus_intf = getattr(ep.decoded.data_memory, name)
            connect_MonitorIntf(intf, to_bus_intf)

        if self.ADD_NAME_MEMORY:
            name_memory = rename_signal(self, name_memory, "name_memory")
            name_memory_reader = ep.decoded.name_memory
            If(self.clk._onRisingEdge(),
                If(name_memory_reader.en,
                   name_memory_reader.dout(
                       name_memory[name_memory_reader.addr])
                   )
               )

        propagateClkRstn(self)

    @classmethod
    def _build_name_memory(cls, intf: Interface, offset: int):
        if isinstance(intf, Interface) and intf._interfaces:
            res = {}
            for i in intf._interfaces:
                offset, _i = cls._build_name_memory(i, offset)
                res[i._name] = _i
            return offset, res
        else:
            w = intf._dtype.bit_length()
            return offset + w, [offset, w]
        return offset

    def build_name_memory_json(self, monitored_data: List[Tuple[Interface, str]]):
        res = {}
        offset = 0
        for i, name, _, _, _ in monitored_data:
            offset, _i = self._build_name_memory(i, offset)
            res[name] = _i
        return res

    def build_name_memory(self, monitored_data: List[Tuple[Interface, str]]):
        res = self.build_name_memory_json(monitored_data)
        res_bytes = json.dumps(res).encode("utf-8")
        DW = self.DATA_WIDTH
        name_data_width = ceil((len(res_bytes) * 8) / DW) * DW
        res = Bits(name_data_width).from_py(
            int.from_bytes(res_bytes, "little"))
        res = res._reinterpret_cast(Bits(DW)[name_data_width // DW])

        return res, name_data_width // 8, len(res_bytes)

    def apply_connections(self):
        """
        Connect a monitored interface to monitor ports of this component
        """
        parent = self._parent
        for intf, (orig_intf, name, cdc, trigger, add_reg) in zip(self.monitor, self.monitored_data):
            if trigger is not None or cdc or add_reg:
                intf_t = Interface_to_HdlType().apply(intf)
            else:
                intf_t = None

            in_clk, in_rst = orig_intf._getAssociatedClk(), orig_intf._getAssociatedRst()
            out_clk, out_rst = self.s._getAssociatedClk(), self.s._getAssociatedRst()
            if not cdc and trigger is not None:
                # regiter where trigger is en
                reg = parent._reg(name, intf_t, clk=in_clk, rst=in_rst)
                If(trigger,
                   *connect_to_MonitorIntf(orig_intf, reg)
                   )
                orig_intf = reg

            if cdc:
                # synchronize input signals to clock domain of this component
                cdc_inst = MonitorIntfVldSyncedCdc(orig_intf)
                cdc_inst.IN_FREQ = in_clk.FREQ
                cdc_inst.OUT_FREQ = out_clk.FREQ
                # ignore because we can do anything about
                cdc_inst.IGNORE_DATA_LOSE = True

                setattr(parent, "cdc_" + name, cdc_inst)
                cdc_inst.dataIn_clk(in_clk)
                cdc_inst.dataIn_rst_n(in_rst)
                if trigger is not None:
                    cdc_inst.dataIn.vld(trigger)
                else:
                    cdc_inst.dataIn.vld(1)
                connect_to_MonitorIntf(orig_intf, cdc_inst.dataIn.data)

                cdc_inst.dataOut_clk(out_clk)
                cdc_inst.dataOut_rst_n(out_rst)

                orig_intf = cdc_inst.dataOut.data

            if add_reg:
                reg = parent._reg(name + "_reg", intf_t,
                                  clk=out_clk, rst=out_rst)
                connect_to_MonitorIntf(orig_intf, reg)
                orig_intf = reg
            # connect to this component
            connect_to_MonitorIntf(orig_intf, intf)
