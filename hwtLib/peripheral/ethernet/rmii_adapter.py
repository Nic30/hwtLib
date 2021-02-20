from math import ceil

from hwt.code import If, Concat, rol, Switch, In
from hwt.hdl.operatorDefs import AllOps
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.enum import HEnum
from hwt.interfaces.utils import addClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axis import AxiStream
from hwtLib.peripheral.ethernet.constants import ETH
from hwtLib.peripheral.ethernet.rmii import Rmii
from hwtLib.peripheral.ethernet.vldsynced_data_err_last import VldSyncedDataErrLast
from pyMathBitPrecise.bit_utils import mask


class RmiiAdapter(Unit):
    """
    Convertor which converts RMII interface to a simple AxiStream/VldSynced interface

    :note: handles CDC, Tx IPG (Inter packet grap), RMII Tx/Rx logic,
        add/remove preamble and SFD
    :attention: inside of packet the tx.vld has to stay 1
        otherwise the underflow error will appear and frame data will
        be corrupted
    :ivar ~.FREQ: specifies the clk.FREQ for this core,
        f None it means that clk and eth.ref_clk is the same signal
        and synchronisation is not required
    :ivar ~.ASYNC_BUFF_DEPTH: depth of asynchronous buffers
        between eth.ref_clk clock domain and clk domain
        (if set to None the clock domain has to be the same)

    .. hwt-autodoc::
    """

    def _config(self):
        self.FREQ = Param(None)
        self.ASYNC_BUFF_DEPTH = Param(None)

    def _declr(self):
        addClkRstn(self)
        self.eth = Rmii()._m()

        if self.FREQ is None:
            self.clk.FREQ = self.eth.FREQ
        else:
            self.clk.FREQ = self.FREQ

        self.tx = AxiStream()
        self.rx = VldSyncedDataErrLast()._m()
        for ch in [self.rx, self.tx]:
            ch.DATA_WIDTH = 8

    def _tx_ipg_logic(self, clk_edge, tx: AxiStream, tx_last_bits: RtlSignal, RMII_W):
        """
        Tx IPG (Inter Packet Gap) logic,
        wait 96 bit times before sending next packet
        """
        cntr_max = ceil(96 / RMII_W) - 1
        tx_ipg_cntr = self._reg("tx_ipg_cntr", Bits(log2ceil(cntr_max), signed=False),
                                def_val=cntr_max,
                                clk=(self.eth.ref_clk, clk_edge))
        If(tx.valid & tx.last & tx_last_bits,
           tx_ipg_cntr(cntr_max),
        ).Elif(tx_ipg_cntr != 0,
           tx_ipg_cntr(tx_ipg_cntr - 1)
        )
        tx_ipg_en = self._sig("tx_ipg_en")
        tx_ipg_en(tx_ipg_cntr._eq(0))
        return tx_ipg_en

    def _tx_logic(self, rmii: Rmii, tx: AxiStream, D_W: int, RMII_W: int, clk_edge):
        CNTR_W = D_W // RMII_W
        clk = (rmii.ref_clk, clk_edge)
        tx_reg = self._reg("tx_reg", Bits(D_W, signed=False),
                           def_val=0, clk=clk)
        tx_vld = self._reg("tx_vld", Bits(CNTR_W, signed=False),
                           def_val=0, clk=clk)
        tx_last_bits = tx_vld._eq(1)
        # last_prev=1 -> sending last byte
        last_prev = self._reg("tx_last_prev", def_val=0)
        tx_ipg_en = self._tx_ipg_logic(clk_edge, tx, last_prev, RMII_W)
        # 7B preable + 1B SFD
        PREAMBLE_CNTR_MAX = 7 + 1
        preamble_cntr = self._reg("tx_preamble_cntr",
                                  dtype=Bits(log2ceil(PREAMBLE_CNTR_MAX), signed=False),
                                  def_val=PREAMBLE_CNTR_MAX - 1,
                                  clk=clk)
        tx_ready = preamble_cntr._eq(0) & (tx_last_bits | tx_vld._eq(0))
        tx.ready(tx_ready)
        If(tx_ready & tx.valid,
           last_prev(tx.last),
        )
        If(tx_ipg_en & tx.valid,
            If(tx_vld._eq(0),
                # start sending new byte
                tx_vld(mask(CNTR_W)),
                If(preamble_cntr._eq(0),
                   tx_reg(tx.data)
                ).Else(
                    tx_reg(ETH.PREAMBLE_1B)
                )
            ).Elif(tx_last_bits,
                # directly start sending next byte
                # (only if it is data from same frame)
                If(last_prev,
                   tx_vld(0),
                ).Else(
                    tx_vld(mask(CNTR_W)),
                ),
                Switch(preamble_cntr)\
                .Case(0,
                      # preambule already send
                      tx_reg(tx.data)
                ).Case(1,
                       tx_reg(ETH.SFD)
                ).Default(
                        tx_reg(ETH.PREAMBLE_1B)
                ),
                If(preamble_cntr != 0,
                   preamble_cntr(preamble_cntr - 1)
                )
            ).Else(
                # continue sending current data from tx_reg
                tx_vld(tx_vld >> 1),
                tx_reg(tx_reg >> RMII_W),
            )
        ).Else(
            preamble_cntr(PREAMBLE_CNTR_MAX - 1),
            tx_vld(tx_vld >> 1),
            tx_reg(tx_reg >> RMII_W),
        )
        rmii.tx.d(tx_reg[RMII_W:])
        rmii.tx.en(tx_vld != 0)

    def _rx_logic(self, rmii: Rmii, rx: VldSyncedDataErrLast,
                  D_W: int, RMII_W: int, clk_edge):
        CNTR_W = D_W // RMII_W

        clk = (rmii.ref_clk, clk_edge)
        # register for all input signals
        din = self._reg("rx_din", Bits(RMII_W), clk=clk)
        din_vld = self._reg("rx_din_vld", clk=clk, def_val=0)
        din(rmii.rx.d)
        din_vld(rmii.rx.crs_dv)

        # register for temporary RX byte
        reg0 = self._reg("rx_reg0", Bits(D_W, signed=False),
                         def_val=0,
                         clk=clk)
        # register for Rx byte for clock edge sync
        reg1 = self._reg("rx_reg1", Bits(D_W, signed=False),
                         def_val=0,
                         clk=rmii.ref_clk)
        reg1_vld = self._reg("rx_reg1_vld", def_val=0)
        # one hot counter with rotating 1
        cntr = self._reg("rx_cntr", Bits(CNTR_W, signed=False),
                         def_val=1,
                         clk=clk)
        # counter of preambule bytes
        preamble_cnt = self._reg("rx_preamble_cntr",
                                 Bits(log2ceil(8), signed=False),
                                 clk=clk)

        st_t = HEnum("rx_state_t", ["skip0", "preamble_and_sfd", "data", "error"])
        st = self._reg("rx_state", st_t, def_val=st_t.skip0, clk=clk)
        last_in_B = cntr[CNTR_W - 1] & din_vld
        actual_rx_B = self._sig("rx_actual_val", dtype=Bits(8))
        actual_rx_B(Concat(din, reg0[:RMII_W]))

        Switch(st)\
        .Case(st_t.skip0,
            If(din_vld & (din != 0),
               st(st_t.preamble_and_sfd),
               preamble_cnt(8-1),
            ),
        ).Case(st_t.preamble_and_sfd,
            If(last_in_B,
                If(preamble_cnt._eq(0),
                    If(actual_rx_B != ETH.SFD,
                       st(st_t.error)
                    ).Else(
                       st(st_t.data)
                    )
                ).Elif(actual_rx_B != ETH.PREAMBLE_1B,
                    st(st_t.error),
                ),
                preamble_cnt(preamble_cnt - 1)
            )
        ).Case(st_t.error,
            If(~din_vld,
               st(st_t.skip0),
            )
        ).Case(st_t.data,
            If(cntr[CNTR_W - 1] & ~din_vld,
               st(st_t.skip0)
            )
        )

        # bit collection logic
        If(st._eq(st_t.skip0),
            cntr(1<<1),
            reg0(Concat(din, Bits(D_W - RMII_W).from_py(0))),
        ).Elif(In(st, [st_t.preamble_and_sfd, st_t.data]),
            # shift in LSB first
            # :note: only D_W - RMII_W bits is captured in reg0
            reg0(Concat(din, reg0[:RMII_W])),
            cntr(rol(cntr, 1)),
        )

        reg1_vld(st._eq(st_t.data) & last_in_B)
        If(reg1_vld.next,
           reg1(actual_rx_B),
        )
        err = st._eq(st_t.error)
        If(err,
            rx.data(None),
        ).Else(
            rx.data(reg1)
        )

        rx.err(err)
        rx.last(~din_vld)
        rx.vld(reg1_vld | st._eq(st_t.error))

    def _impl(self):
        assert self.clk.FREQ >= self.eth.ref_clk.FREQ, (
                self.clk.FREQ, self.eth.ref_clk.FREQ,
                "Has to have same or faster frequency "
                "otherwise data will be corrupted during Rx/Tx")

        rmii = self.eth
        RMII_W = rmii.DATA_WIDTH
        D_W = self.tx.DATA_WIDTH
        assert D_W % RMII_W == 0, (D_W, RMII_W)
        self._tx_logic(rmii, self.tx, D_W, RMII_W, AllOps.FALLING_EDGE)
        self._rx_logic(rmii, self.rx, D_W, RMII_W, AllOps.RISING_EDGE)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = RmiiAdapter()
    print(to_rtl_str(u))
