#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Concat
from hwt.constants import READ_WRITE, WRITE, READ
from hwt.hObjList import HObjList
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOBramPort, HwIOClk, HwIOBramPort_noClk
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal


@serializeParamsUniq
class RamSingleClock(HwModule):
    """
    RAM/ROM with only one clock signal.
    It can be configured to have arbitrary number of ports.
    It can also be configured to have write mask or to be composed from multiple smaller memories.


    :note: This memory may not be mapped to RAM
        if synthesis tool consider it to be too small.

    :ivar PORT_CNT: HwParam which specifies number of ram ports,
        it can be int or tuple of READ_WRITE, WRITE, READ
        to specify rw access for each port separately
    :ivar HAS_BE: HwParam, if True the write ports will have byte enable signal
    :ivar READ_LATENCY: latency in clock cycles from read enable=1 to read data appear on the output
        0=distmem, 1=BRAM
    .. hwt-autodoc::
    """
    PORT_CLS = HwIOBramPort_noClk

    @override
    def hwConfig(self):
        self.ADDR_WIDTH = HwParam(10)
        self.DATA_WIDTH = HwParam(64)
        self.PORT_CNT = HwParam(1)
        self.HAS_BE = HwParam(False)
        self.MAX_BLOCK_DATA_WIDTH = HwParam(None)
        self.INIT_DATA = HwParam(None)
        self.READ_LATENCY = HwParam(1)

    def _declr_ports(self):
        PORTS = self.PORT_CNT
        with self._hwParamsShared():
            ports = HObjList()
            if isinstance(PORTS, int):
                for _ in range(PORTS):
                    p = self.PORT_CLS()
                    ports.append(p)
            else:
                for access_mode in PORTS:
                    p = self.PORT_CLS()
                    if access_mode == READ_WRITE:
                        pass
                    elif access_mode == READ:
                        p.HAS_W = False
                    elif access_mode == WRITE:
                        p.HAS_R = False
                    else:
                        raise ValueError(access_mode)

                    ports.append(p)
            self.port = ports

    def _declr_children(self):
        # for the case where this memory will be realized using multiple memory blocks
        children = HObjList()
        MAX_DW = self.MAX_BLOCK_DATA_WIDTH
        if MAX_DW is not None and MAX_DW < self.DATA_WIDTH:
            DW = self.DATA_WIDTH
            while DW > 0:
                c = self.__class__()
                c._updateHwParamsFrom(self, exclude=({"DATA_WIDTH"}, {}))
                c.DATA_WIDTH = min(DW, MAX_DW)
                if self.INIT_DATA is not None:
                    raise NotImplementedError()
                children.append(c)
                DW -= MAX_DW
        self.children = children

    @override
    def hwDeclr(self):
        self.clk = HwIOClk()
        self._declr_ports()
        self._declr_children()

    @staticmethod
    def mem_write(mem, port: HwIOBramPort_noClk):
        drive = []
        if port.HAS_BE:
            assert port.DATA_WIDTH % 8 == 0, port.DATA_WIDTH
            # we for each byte separate
            # drive.append(
            #    mem[port.addr](apply_write_with_mask(mem[port.addr], port.din, port.we))
            # )
            for b_i, be in enumerate(port.we):
                low = b_i * 8
                drive.append(
                    If(be,
                       mem[port.addr][low + 8: low](port.din[low + 8: low])
                    )
                )
        elif port.HAS_R and port.HAS_W:
            # explicit we
            drive.append(
                If(port.we,
                   mem[port.addr](port.din)
                )
            )
        else:
            # en used as we
            drive.append(mem[port.addr](port.din))

        return drive

    @staticmethod
    def connect_HwIOBramPort_noClk_to_mem(clk: RtlSignal, read_latency, port: HwIOBramPort_noClk, mem: RtlSignal):
        if port.HAS_R and port.HAS_W:
            rStm = \
            If(port.en,
                *RamSingleClock.mem_write(mem, port),
                port.dout(mem[port.addr]),
            ).Else(
                port.dout(None),
            ),
        elif port.HAS_R:
            rStm = \
            If(port.en,
                port.dout(mem[port.addr])
            )
        elif port.HAS_W:
            rStm = \
            If(port.en,
               *RamSingleClock.mem_write(mem, port),
            )
        else:
            raise AssertionError("Bram port has to have at least write or read part")

        if read_latency == 0:
            pass
        elif read_latency == 1:
            If(clk._onRisingEdge(),
               rStm
            )
        else:
            raise NotImplementedError(read_latency)

    def delegate_to_children(self):
        MAX_DW = self.MAX_BLOCK_DATA_WIDTH
        DW = self.DATA_WIDTH

        for ports in zip(self.port, *[c.port for c in self.children]):
            dout = []
            p = ports[0]
            clk = getattr(p, "clk", None)

            for i, cp in enumerate(ports[1:]):
                cp.en(p.en)
                cp.addr(p.addr)
                if p.HAS_R:
                    dout.append(cp.dout)
                if p.HAS_W:
                    if p.HAS_BE:
                        cp.we(p.we[min((i + 1) * (MAX_DW // 8), DW // 8):i * (MAX_DW // 8)])
                    elif p.HAS_R:
                        cp.we(p.we)
                    cp.din(p.din[min((i + 1) * (MAX_DW), DW):i * (MAX_DW)])
                if clk is not None:
                    cp.clk(clk)

            if dout:
                p.dout(Concat(*reversed(dout)))

        clk = getattr(self, "clk", None)
        for c in self.children:
            c.clk(clk)

    @override
    def hwImpl(self):
        if self.children:
            self.delegate_to_children()
        else:
            dt = HBits(self.DATA_WIDTH)[2 ** self.ADDR_WIDTH]
            self._mem = self._sig("ram_memory", dt, def_val=self.INIT_DATA)

            for p in self.port:
                self.connect_HwIOBramPort_noClk_to_mem(self.clk, self.READ_LATENCY, p, self._mem)


@serializeParamsUniq
class RamMultiClock(HwModule):
    """
    RAM where each port has an independent clock.
    It can be configured to true dual port RAM etc.
    It can also be configured to have write mask or to be composed from multiple smaller memories.

    :note: write-first variant

    .. hwt-autodoc::
    """
    PORT_CLS = HwIOBramPort

    @override
    def hwConfig(self):
        RamSingleClock.hwConfig(self)
        self.PORT_CNT = 2

    @override
    def hwDeclr(self):
        RamSingleClock._declr_ports(self)
        RamSingleClock._declr_children(self)

    @override
    def hwImpl(self):
        if self.children:
            self.delegate_to_children()
        else:
            dt = HBits(self.DATA_WIDTH)[2 ** self.ADDR_WIDTH]
            self._mem = self._sig("ram_memory", dt, self.INIT_DATA)

            for p in self.port:
                RamSingleClock.connect_HwIOBramPort_noClk_to_mem(p.clk, self.READ_LATENCY, p, self._mem)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str

    m = RamSingleClock()
    m.HAS_BE = True
    m.ADDR_WIDTH = 10
    m.DATA_WIDTH = 17 * 8
    print(to_rtl_str(m))
