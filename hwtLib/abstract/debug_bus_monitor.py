import json
from math import ceil
from typing import List, Tuple, Optional, Union, Dict

from hwt.code import If
from hwt.code_utils import rename_signal
from hwt.hObjList import HObjList
from hwt.hdl.types.bits import HBits
from hwt.hwIO import HwIO
from hwt.hwIOs.hwIOStruct import HwIO_to_HdlType
from hwt.hwIOs.hwIO_map import HwIOObjMap, HTypeFromHwIOObjMap
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.mainBases import HwIOBase
from hwt.pyUtils.typingFuture import override
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwtLib.abstract.hwIOMonitor import monitor_of, connect_HwIOMonitor, \
    connect_to_HwIOMonitor, HwIOMonitorDataVldCdc


class DebugBusMonitorDataRecord():

    def __init__(self, hwIO: HwIO, name: str, cdc: bool, trigger: RtlSignal, add_reg: bool):
        self.parent = None
        self.hwIO = hwIO
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
        return self.hwIO is None

    def add_link(self, dst: "DebugBusMonitorDataRecord"):
        assert isinstance(dst, DebugBusMonitorDataRecord), dst
        self.successors.append(dst)


class DebugBusMonitor(HwModule):
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
        self.visual_containers: Dict[Union[HwModule, HwIO]] = {}
        super(DebugBusMonitor, self).__init__()

    @override
    def hwConfig(self):
        self._bus_cls.hwConfig(self)
        self.monitored_data: List[DebugBusMonitorDataRecord] = []
        self.ADD_META_MEMORY: bool = HwParam(True)

    def register(self, hwIO: HwIO,
                 name: Optional[str]=None,
                 cdc: bool=False,
                 trigger: Optional[RtlSignal]=None,
                 add_reg: bool=False):
        """
        :param hwIO: an interface to monitor
        :param name: name override
        :param cdc: if True instantiate Clock domain crossing to synchronize input
            data to clock domain of this component
        :param trigger: an optional signal which triggers the snapshot of this interface
        :note: if cdc is set to True the trigger has to be synchonezed to a clock clock domain of hwIO
        :param add_reg: if True an register is added between input and bus interface
        """
        assert not self.io_instantiated
        if name is None:
            if isinstance(hwIO, HwIOBase):
                name = hwIO._getHdlName()
            else:
                name = hwIO.name
        d = DebugBusMonitorDataRecord(hwIO, name, cdc, trigger, add_reg)
        self.monitored_data.append(d)
        return d

    @override
    def hwDeclr(self):
        addClkRstn(self)
        with self._hwParamsShared():
            self.s = self._bus_cls()
        # declare an interface with same signals but all inputs for each
        # monitored interface
        self.monitor = HObjList([
            monitor_of(d.hwIO) for d in self.monitored_data if not d.is_visual_only()
        ])
        self.io_instantiated = True

    @override
    def hwImpl(self):
        if self.ADD_META_MEMORY:
            meta_memory, meta_memory_size, name_content_size = \
                self.build_meta_memory(self.monitored_data)
        else:
            name_content_size = 0
        const_uint32_t = HBits(32, signed=False, const=True)
        addr_space = HwIOObjMap([
            (const_uint32_t, "meta_memory_size"),
            (const_uint32_t, "meta_memory_offset"),
            (HwIOObjMap(
                (HwIO_to_HdlType().apply(d.hwIO, const=True), d.name)
                for d in self.monitored_data if not d.is_visual_only()
            ), "data_memory"),
        ])
        data_part_t = HTypeFromHwIOObjMap(addr_space)
        data_part_width = data_part_t.bit_length()
        if self.ADD_META_MEMORY:
            closest_pow2 = 2 ** data_part_width.bit_length()
            if data_part_width != closest_pow2:
                # padding between data_memory and meta_memory
                addr_space.append((HBits(closest_pow2 - data_part_width), None))
            meta_memory_offset = closest_pow2 // 8

            meta_mem_words = meta_memory_size // (self.DATA_WIDTH // 8)
            addr_space.append(
                (HBits(self.DATA_WIDTH, const=True)[meta_mem_words],
                 "meta_memory")
            )
        else:
            meta_memory_offset = 0

        ep = self._bus_endpoint_cls.fromHwIOMap(addr_space)

        with self._hwParamsShared():
            self.ep = ep
        ep.bus(self.s)

        ep.decoded.meta_memory_size(name_content_size)
        ep.decoded.meta_memory_offset(meta_memory_offset)
        for hwIO, d in self.iter_monitor_HwIOs():
            to_bus_HwIO = getattr(ep.decoded.data_memory, d.name)
            connect_HwIOMonitor(hwIO, to_bus_HwIO)

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
    def _build_meta_memory(cls, hwIO: HwIO, offset: int):
        if isinstance(hwIO, HwIO) and hwIO._hwIOs:
            res = []
            for cHwIO in hwIO._hwIOs:
                offset, _i = cls._build_meta_memory(cHwIO, offset)
                res.append((cHwIO._name, _i))

            return offset, res

        else:
            w = hwIO._dtype.bit_length()
            return offset + w, [offset, w]

        return offset

    def build_meta_memory_json(self,
                               monitored_data: List[DebugBusMonitorDataRecord],
                               data_ids: Dict[DebugBusMonitorDataRecord, int],
                               offset: int):
        res = []
        for d in monitored_data:
            d: DebugBusMonitorDataRecord

            if d.is_visual_only():
                _i = []
            else:
                offset, _i = self._build_meta_memory(d.hwIO, offset)

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
        res = HBits(name_data_width).from_py(
            int.from_bytes(res_bytes, "little"))
        res = res._reinterpret_cast(HBits(DW)[name_data_width // DW])

        return res, name_data_width // 8, len(res_bytes)

    def iter_monitor_HwIOs(self):
        yield from zip(self.monitor, (_d for _d in self.monitored_data if not _d.is_visual_only()))

    def apply_connections(self):
        """
        Connect a monitored interface to monitor ports of this component
        """
        parent = self._parent
        for hwIO, d in self.iter_monitor_HwIOs():
            if d.trigger is not None or d.cdc or d.add_reg:
                hwIO_t = HwIO_to_HdlType().apply(hwIO)
            else:
                hwIO_t = None

            in_clk, in_rst = d.hwIO._getAssociatedClk(), d.hwIO._getAssociatedRst()
            out_clk, out_rst = self.s._getAssociatedClk(), self.s._getAssociatedRst()
            origHwIO = d.hwIO
            if not d.cdc and d.trigger is not None:
                # regiter where trigger is en
                reg = parent._reg(d.name, hwIO_t, clk=in_clk, rst=in_rst)
                If(d.trigger,
                   *connect_to_HwIOMonitor(d.hwIO, reg)
                   )
                origHwIO = reg

            if d.cdc:
                # synchronize input signals to clock domain of this component
                cdc_inst = HwIOMonitorDataVldCdc(origHwIO)
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
                connect_to_HwIOMonitor(origHwIO, cdc_inst.dataIn.data)

                cdc_inst.dataOut_clk(out_clk)
                cdc_inst.dataOut_rst_n(out_rst)

                origHwIO = cdc_inst.dataOut.data

            if d.add_reg:
                reg = parent._reg(d.name + "_reg", hwIO_t,
                                  clk=out_clk, rst=out_rst)
                connect_to_HwIOMonitor(origHwIO, reg)
                origHwIO = reg
            # connect to this component
            connect_to_HwIOMonitor(origHwIO, hwIO)
