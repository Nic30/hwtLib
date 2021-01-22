from math import ceil

from hwt.code import FsmBuilder, Concat, If, In
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.enum import HEnum
from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.std import VectSignal, HandshakeSync, \
    Handshaked
from hwt.interfaces.utils import addClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.clocking.clkBuilder import ClkBuilder
from hwtLib.peripheral.mdio.intf import Mdio
from hwtSimApi.hdlSimulator import HdlSimulator


class MdioAddr(Interface):
    """
    .. hwt-autodoc::
    """

    def _declr(self):
        self.phy = VectSignal(5)
        self.reg = VectSignal(5)


class MdioReq(HandshakeSync):
    """
    MDIO transaction request interface

    .. hwt-autodoc::
    """

    def _declr(self):
        self.opcode = VectSignal(Mdio.OP_W)  # R/W
        self.addr = MdioAddr()
        self.wdata = VectSignal(Mdio.D_W)
        HandshakeSync._declr(self)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = MdioReqAgent(sim, self)


class MdioReqAgent(HandshakedAgent):
    """
    Simulation agent for :class:`.MdioReq` interface
    """
    def set_data(self, data):
        i = self.intf
        if data is None:
            i.opcode.write(None)
            i.addr.phy.write(None)
            i.addr.reg.write(None)
            i.wdata.write(None)
        else:
            opcode, (phyaddr, regaddr), wdata = data
            i.opcode.write(opcode)
            i.addr.phy.write(phyaddr)
            i.addr.reg.write(regaddr)
            i.wdata.write(wdata)

    def get_data(self):
        i = self.intf
        return (i.opcode.read(),
                (i.addr.phy.read(), i.addr.reg.read()),
                i.wdata.read())


def shift_in_msb_first(reg, sig_in):
    """
    Shift data in to register, MSB first
    """
    w = reg._dtype.bit_length()
    w_in = sig_in._dtype.bit_length()
    return reg(Concat(reg[w-w_in:], sig_in))


class MdioMaster(Unit):
    """
    Master for MDIO interface.

    :ivar ~.FREQ: frequency of input clock
    :ivar ~.MDIO_FREQ: frequency of output MDIO clock

    * based on:
        * https://opencores.org/websvn/filedetails?repname=ethmac10g&path=%2Fethmac10g%2Ftrunk%2Frtl%2Fverilog%2Fmgmt%2Fmdio.v
        * https://github.com/NetFPGA/netfpga/blob/master/lib/verilog/core/io/mdio/src/nf2_mdio.v

    .. hwt-autodoc::
    """


    def _config(self):
        self.FREQ = Param(int(100e6))
        self.MDIO_FREQ = Param(int(2.5e6))

    def _declr(self):
        addClkRstn(self)
        self.md = Mdio()._m()
        self.rdata = Handshaked()._m()
        self.rdata.DATA_WIDTH = Mdio.D_W
        self.req = MdioReq()

    def _packet_sequence_timer(self,
                               mdio_clk_rising,
                               mdio_clk_falling, rst_n):
        """
        Create timers for all important events in protocol main FSM
        """
        PRE_W = Mdio.PRE_W
        ADDR_BLOCK_W = Mdio.ADDR_BLOCK_W
        TA_W = Mdio.TA_W
        preamble_last = self._sig("preamble_last")
        addr_block_last = self._sig("addr_block_last")
        turnarround_last_en = self._sig("turnarround_last_en")
        data_last = self._sig("data_last")

        CNTR_MAX = PRE_W + ADDR_BLOCK_W + TA_W + Mdio.D_W - 1
        timer = self._reg("packet_sequence_timer",
                          dtype=Bits(log2ceil(CNTR_MAX)),
                          def_val=0, rst=self.rst_n & rst_n)
        If(mdio_clk_falling,
           timer(timer + 1)
        )
        preamble_last(mdio_clk_falling & timer._eq(PRE_W - 1))
        addr_block_last(mdio_clk_falling & timer._eq(PRE_W + ADDR_BLOCK_W - 1))
        turnarround_last_en(timer._eq(PRE_W + ADDR_BLOCK_W + TA_W - 1))
        data_last(mdio_clk_rising & timer._eq(CNTR_MAX))

        return preamble_last, addr_block_last, turnarround_last_en, data_last

    def _impl(self):
        # timers and other registers
        CLK_HALF_PERIOD_DIV = ceil(self.clk.FREQ / (self.MDIO_FREQ * 2))
        mdio_clk = self._reg("mdio_clk", def_val=0)
        r_data_vld = self._reg("r_data_vld", def_val=0)
        req = self.req
        clk_half_period_en = ClkBuilder(self, self.clk).timer(
            ("clk_half_period_en", CLK_HALF_PERIOD_DIV))
        If(clk_half_period_en,
            mdio_clk(~mdio_clk),
        )
        mdio_clk_rising = clk_half_period_en & ~mdio_clk
        mdio_clk_falling = clk_half_period_en & mdio_clk
        idle = self._sig("idle")
        preamble_last, addr_block_last, turnarround_last_en, data_last =\
            self._packet_sequence_timer(
                mdio_clk_rising, mdio_clk_falling, ~idle)
        is_rx = self._reg("is_rx", def_val=0)

        # protocol FSM
        st_t = HEnum("st_t", ["idle", "pre", "addr_block", "ta", "data"])
        st = FsmBuilder(self, st_t)\
            .Trans(st_t.idle, (req.vld & ~r_data_vld, st_t.pre))\
            .Trans(st_t.pre, (preamble_last, st_t.addr_block))\
            .Trans(st_t.addr_block, (addr_block_last, st_t.ta))\
            .Trans(st_t.ta, (turnarround_last_en & (
                                (is_rx & mdio_clk_falling)
                                | (~is_rx & mdio_clk_rising)), st_t.data))\
            .Trans(st_t.data, (data_last, st_t.idle)).stateReg

        idle(st._eq(st_t.idle))
        req.rd(idle & ~r_data_vld)
        If(idle,
           is_rx(req.opcode._eq(Mdio.OP.READ))
        )

        # TX logic
        md = self.md
        TX_W = md.ST_W + md.OP_W + md.PA_W + md.RA_W + md.TA_W + md.D_W
        tx_reg = self._reg("tx_reg", Bits(TX_W))
        If(idle & req.vld,
            tx_reg(Concat(Mdio.ST, req.opcode, req.addr.phy,
                          req.addr.reg, Mdio.TA, req.wdata))
        ).Elif(mdio_clk_falling & In(st, [st_t.addr_block, st_t.data, st_t.ta, st_t.data]),
            tx_reg(tx_reg << 1)
        )
        md.c(mdio_clk)

        # because MDIO uses open-drain, this means that if t=0 the value of the signal is 1
        md.io.o(0)
        tx_bit = tx_reg[tx_reg._dtype.bit_length() - 1]
        md.io.t(~idle & ~tx_bit & (st._eq(st_t.addr_block)
                                   | (In(st, [st_t.data, st_t.ta]) & ~is_rx))
        )

        # RX logic
        rx_reg = self._reg("rx_reg", Bits(md.D_W))
        If(st._eq(st_t.data) & is_rx & mdio_clk_rising,
           shift_in_msb_first(rx_reg, self.md.io.i)
        )

        If(idle & self.rdata.rd,
            r_data_vld(0)
        ).Elif(addr_block_last,
            r_data_vld(is_rx)
        )
        self.rdata.vld(idle & r_data_vld)
        self.rdata.data(rx_reg)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = MdioMaster()
    print(to_rtl_str(u))
