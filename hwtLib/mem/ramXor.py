#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Xor
from hwt.hdl.constants import READ_WRITE, WRITE, READ
from hwt.interfaces.utils import propagateClk, addClkRst
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwtLib.mem.ram import RamSingleClock


@serializeParamsUniq
class RamXorSingleClock(RamSingleClock):
    """
    Multiport XOR based RAM with only one clock signal

    :note: XOR, LVT, multipumped, banked and similar multiport memory implementations
        are used to build a more memory ported memories from memories available.
        https://doi.org/10.1145/2145694.2145730
        https://doi.org/10.1145/2629629

    :note: The bitwise XOR operation is commutative, associative, and hasthe following properties
        1. A^0 = A
        2. B^B = 0
        3. A^B^B=A
        The third property, which follows from the first two, implies that we can XOR two values A and B together,
        and recover A by XORing the result with B. This componnet uses this principe to generate additional write ports.

    :see: :class:`~.RamSingleClock`

    .. hwt-autodoc::
    """

    def _config(self):
        RamSingleClock._config(self)
        self.PORT_CNT = (WRITE, WRITE, READ)
        self.PRIMITIVE_MEMORY_PORTS = Param((WRITE, READ))

    def _declr(self):
        addClkRst(self)
        self._declr_ports()

        r_ports = []
        w_ports = []
        rw_ports = []

        for p in self.port:
            if p.HAS_R and p.HAS_W:
                rw_ports.append(p)
            else:
                if p.HAS_R:
                    r_ports.append(p)

                if p.HAS_W:
                    w_ports.append(p)

        self._r_ports = r_ports
        self._w_ports = w_ports
        self._rw_ports = rw_ports

        primitive_ram_r_port_i = []
        primitive_ram_w_port_i = []
        primitive_ram_rw_port_i = []
        if isinstance(self.PRIMITIVE_MEMORY_PORTS, int):
            primitive_ram_rw_port_i = list(range(self.PRIMITIVE_MEMORY_PORTS))
        else:
            for i, p in enumerate(self.PRIMITIVE_MEMORY_PORTS):
                if p == READ:
                    primitive_ram_r_port_i.append(i)
                elif p == WRITE:
                    primitive_ram_w_port_i.append(i)
                elif p == READ_WRITE:
                    primitive_ram_rw_port_i.append(i)
                else:
                    raise NotImplementedError(p)

        can_be_primitive_ram = len(rw_ports) <= len(primitive_ram_rw_port_i) and \
                               len(r_ports) <= len(primitive_ram_r_port_i) and \
                               len(w_ports) <= len(primitive_ram_w_port_i)
        self._can_be_primitive_ram = can_be_primitive_ram
        if can_be_primitive_ram:
            self._declr_children()

    def _impl(self):
        if self._can_be_primitive_ram:
            super(RamXorSingleClock, self)._impl()
        else:
            if self.PRIMITIVE_MEMORY_PORTS != (WRITE, READ):
                raise NotImplementedError(self.PRIMITIVE_MEMORY_PORTS)
            if self._rw_ports:
                raise NotImplementedError("RW ports (supports only write and read ports)")

            r_ports = self._r_ports
            assert r_ports
            w_ports = self._w_ports
            assert w_ports
            # 1. construct a matrix N x N where N is a number of wrie ports
            # the diagonal is set to None because we do not need to synchronize the port with itself
            w_rams = HObjList(
                HObjList(
                    RamSingleClock() if x != y else None
                    for x in w_ports
                )
                for y in w_ports)
            # construct a matrix M x N where M is number of read ports
            r_rams = HObjList(HObjList(RamSingleClock() for _ in w_ports)
                              for _ in range(len(r_ports)))

            for row in w_rams + r_rams:
                for r in row:
                    if r is None:
                        continue
                    r._updateParamsFrom(self, exclude=(("PORT_CNT",), ()))
                    r.PORT_CNT = self.PRIMITIVE_MEMORY_PORTS
                    if self.INIT_DATA is not None:
                        raise NotImplementedError()
                    r.INIT_DATA = tuple(0 for _ in range(2 ** r.ADDR_WIDTH))
            self.w_rams = w_rams
            self.r_rams = r_rams

            # :type: List[Tuple[RtlSignal, RtlSignal, RtlSignal]]
            # List of tuples (en, address, write data), used for write forwarding on read ports
            write_in_progress_staus = []

            # 2. connect them with XOR logic
            # add the register on write address and data because we need to load the data for XOR first
            for i, w in enumerate(w_ports):
                xor_src = []
                for mem in w_rams[i]:
                    if mem is not None:
                        xor_src.append(mem)

                xor_loaded_src = []
                for s in xor_src:
                    p = s.port[1]
                    p.addr(w.addr)
                    p.en(w.en)
                    xor_loaded_src.append(p.dout)

                w_addr_reg = self._reg(f"{w._name}_addr_reg", w.addr._dtype)
                w_addr_reg(w.addr)
                w_en_reg = self._reg(f"{w._name}_en_reg", def_val=0)
                w_en_reg(w.en)
                w_data_reg = self._reg(f"{w._name}_data_reg", w.din._dtype)
                w_data_reg(w.din)

                xored_data = Xor(w_data_reg, *xor_loaded_src)
                for ram_row in w_rams + r_rams:
                    xor_dst = ram_row[i]
                    if xor_dst is None:
                        continue
                    xor_dst = xor_dst.port[0]
                    xor_dst.addr(w_addr_reg)
                    xor_dst.en(w_en_reg)
                    xor_dst.din(xored_data)
                write_in_progress_staus.append((w_en_reg, w_addr_reg, xored_data))

            # 3. connect read ports to memories
            for (i, r), r_ram_column in zip(enumerate(r_ports), r_rams):
                out_xor_inputs = []
                for r_ram, (w_en_reg, w_addr_reg, w_xored_data) in zip(r_ram_column, write_in_progress_staus):
                    r_ram = r_ram.port[1]
                    s = (w_en_reg & w_addr_reg._eq(r.addr))._ternary(w_xored_data, r_ram.dout)
                    out_xor_inputs.append(s)
                    r_ram.addr(r.addr)
                    r_ram.en(r.en)

                r.dout(Xor(*out_xor_inputs))

            propagateClk(self)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = RamXorSingleClock()
    u.ADDR_WIDTH = 10
    u.DATA_WIDTH = 32
    u.PORT_CNT = (*(WRITE for _ in range(4)), *(READ for _ in range(8)))
    print(to_rtl_str(u))
