import json
from math import ceil
from typing import List, Tuple, Optional, Union, Dict

from hwt.code import If
from hwt.code_utils import rename_signal
from hwt.hdl.types.bits import Bits
from hwt.interfaces.intf_map import IntfMap, HTypeFromIntfMap
from hwt.interfaces.structIntf import Interface_to_HdlType
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.interfaceLevel.mainBases import InterfaceBase
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwtLib.abstract.monitorIntf import monitor_of, connect_MonitorIntf, \
    connect_to_MonitorIntf, MonitorIntfVldSyncedCdc


class DebugBusMonitorDataRecord():

    def __init__(self, intf: Interface, name: str, cdc: bool, trigger: RtlSignal, add_reg: bool):
        self.parent = None
        self.intf = intf
        self.name = name
        self.cdc = cdc
        self.trigger = trigger
        self.add_reg = add_reg
        self.successors: List[DebugBusMonitorDataRecord] = []
        self.children: List[DebugBusMonitorDataRecord] = []

    def add_children(self, c: "DebugBusMonitorDataRecord"):
        c.parent = self
        self.children.append(c)

    def is_visual_only(self):
        return self.intf is None

    def add_link(self, dst: "DebugBusMonitorDataRecord"):
        assert isinstance(dst, DebugBusMonitorDataRecord), dst
        self.successors.append(dst)


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
            uint32_t meta_memory_size;
            uint32_t meta_memory_offset; // offsetof(address_space, data)
            // n can be resolved from content of meta_memory
            // as well as structure of data_memory
            uint8_t data_memory[n];
            // padding to size 2**x
            char meta_memory[meta_memory_size]; // contains a JSON with data info (if ADD_META_MEMORY)
        };

    Example of meta_memory JSON format:

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
        self.visual_containers: Dict[Union[Unit, Interface]] = {}
        super(DebugBusMonitor, self).__init__()

    def _config(self):
        self._bus_cls._config(self)
        self.monitored_data: List[DebugBusMonitorDataRecord] = []
        self.ADD_META_MEMORY: bool = Param(True)

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
        d = DebugBusMonitorDataRecord(intf, name, cdc, trigger, add_reg)
        self.monitored_data.append(d)
        return d

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.s = self._bus_cls()
        # declare an interface with same signals but all inputs for each
        # monitored interface
        self.monitor = HObjList([
            monitor_of(d.intf) for d in self.monitored_data if not d.is_visual_only()
        ])
        self.io_instantiated = True

    def _impl(self):
        if self.ADD_META_MEMORY:
            meta_memory, meta_memory_size, name_content_size = \
                self.build_meta_memory(self.monitored_data)
        else:
            name_content_size = 0
        const_uint32_t = Bits(32, signed=False, const=True)
        addr_space = IntfMap([
            (const_uint32_t, "meta_memory_size"),
            (const_uint32_t, "meta_memory_offset"),
            (IntfMap(
                (Interface_to_HdlType().apply(d.intf, const=True), d.name)
                for d in self.monitored_data if not d.is_visual_only()
            ), "data_memory"),
        ])
        data_part_t = HTypeFromIntfMap(addr_space)
        data_part_width = data_part_t.bit_length()
        if self.ADD_META_MEMORY:
            closest_pow2 = 2 ** data_part_width.bit_length()
            if data_part_width != closest_pow2:
                # padding between data_memory and meta_memory
                addr_space.append((Bits(closest_pow2 - data_part_width), None))
            meta_memory_offset = closest_pow2 // 8

            meta_mem_words = meta_memory_size // (self.DATA_WIDTH // 8)
            addr_space.append(
                (Bits(self.DATA_WIDTH, const=True)[meta_mem_words],
                 "meta_memory")
            )
        else:
            meta_memory_offset = 0

        ep = self._bus_endpoint_cls.fromInterfaceMap(addr_space)

        with self._paramsShared():
            self.ep = ep
        ep.bus(self.s)

        ep.decoded.meta_memory_size(name_content_size)
        ep.decoded.meta_memory_offset(meta_memory_offset)
        for intf, d in self.iter_monitor_interface():
            to_bus_intf = getattr(ep.decoded.data_memory, d.name)
            connect_MonitorIntf(intf, to_bus_intf)

        if self.ADD_META_MEMORY:
            meta_memory = rename_signal(self, meta_memory, "meta_memory")
            meta_memory_reader = ep.decoded.meta_memory
            If(self.clk._onRisingEdge(),
                If(meta_memory_reader.en,
                   meta_memory_reader.dout(
                       meta_memory[meta_memory_reader.addr])
                   )
               )

        propagateClkRstn(self)

    @classmethod
    def _build_meta_memory(cls, intf: Interface, offset: int):
        if isinstance(intf, Interface) and intf._interfaces:
            res = []
            for i in intf._interfaces:
                offset, _i = cls._build_meta_memory(i, offset)
                res.append((i._name, _i))

            return offset, res

        else:
            w = intf._dtype.bit_length()
            return offset + w, [offset, w]

        return offset

    def build_meta_memory_json(self, monitored_data: List[DebugBusMonitorDataRecord], data_ids: Dict[DebugBusMonitorDataRecord, int], offset: int):
        res = []
        for d in monitored_data:
            d: DebugBusMonitorDataRecord

            if d.is_visual_only():
                _i = []
            else:
                offset, _i = self._build_meta_memory(d.intf, offset)

            children, offset = self.build_meta_memory_json(d.children, data_ids, offset)
            res.append({
                "id": data_ids[d],
                "name": d.name,
                "data": _i,
                "links": [data_ids[_d] for _d in d.successors],
                'children': children,
            })

        return res, offset

    def build_meta_memory(self, monitored_data: List[DebugBusMonitorDataRecord]):
        data_ids = {}
        for i, d in enumerate(monitored_data):
            data_ids[d] = i

        res, _ = self.build_meta_memory_json((d for d in monitored_data if d.parent is None), data_ids, 0)
        res_bytes = json.dumps(res).encode("utf-8")
        DW = self.DATA_WIDTH
        name_data_width = ceil((len(res_bytes) * 8) / DW) * DW
        res = Bits(name_data_width).from_py(
            int.from_bytes(res_bytes, "little"))
        res = res._reinterpret_cast(Bits(DW)[name_data_width // DW])

        return res, name_data_width // 8, len(res_bytes)

    def iter_monitor_interface(self):
        yield from zip(self.monitor, (_d for _d in self.monitored_data if not _d.is_visual_only()))

    def apply_connections(self):
        """
        Connect a monitored interface to monitor ports of this component
        """
        parent = self._parent
        for intf, d in self.iter_monitor_interface():
            if d.trigger is not None or d.cdc or d.add_reg:
                intf_t = Interface_to_HdlType().apply(intf)
            else:
                intf_t = None

            in_clk, in_rst = d.intf._getAssociatedClk(), d.intf._getAssociatedRst()
            out_clk, out_rst = self.s._getAssociatedClk(), self.s._getAssociatedRst()
            orig_intf = d.intf
            if not d.cdc and d.trigger is not None:
                # regiter where trigger is en
                reg = parent._reg(d.name, intf_t, clk=in_clk, rst=in_rst)
                If(d.trigger,
                   *connect_to_MonitorIntf(d.intf, reg)
                   )
                orig_intf = reg

            if d.cdc:
                # synchronize input signals to clock domain of this component
                cdc_inst = MonitorIntfVldSyncedCdc(orig_intf)
                cdc_inst.IN_FREQ = in_clk.FREQ
                cdc_inst.OUT_FREQ = out_clk.FREQ
                # ignore because we can do anything about
                cdc_inst.IGNORE_DATA_LOSE = True

                setattr(parent, "cdc_" + d.name, cdc_inst)
                cdc_inst.dataIn_clk(in_clk)
                cdc_inst.dataIn_rst_n(in_rst)
                if d.trigger is not None:
                    cdc_inst.dataIn.vld(d.trigger)
                else:
                    cdc_inst.dataIn.vld(1)
                connect_to_MonitorIntf(orig_intf, cdc_inst.dataIn.data)

                cdc_inst.dataOut_clk(out_clk)
                cdc_inst.dataOut_rst_n(out_rst)

                orig_intf = cdc_inst.dataOut.data

            if d.add_reg:
                reg = parent._reg(d.name + "_reg", intf_t,
                                  clk=out_clk, rst=out_rst)
                connect_to_MonitorIntf(orig_intf, reg)
                orig_intf = reg
            # connect to this component
            connect_to_MonitorIntf(orig_intf, intf)
