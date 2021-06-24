from hwt.code import Switch, If
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.param import Param
from hwt.synthesizer.vectorUtils import fitTo
from hwtLib.abstract.busBridge import BusBridge
from hwtLib.amba.axi4 import Axi4, Axi4_addr
from hwtLib.amba.constants import CACHE_DEFAULT, BURST_INCR, LOCK_DEFAULT, \
    PROT_DEFAULT, QOS_DEFAULT, BYTES_IN_TRANS, RESP_DECERR, RESP_SLVERR, \
    RESP_EXOKAY, RESP_OKAY
from hwtLib.avalon.mm import AvalonMM, RESP_SLAVEERROR, RESP_DECODEERROR, RESP_OKAY as AVMM_RESP_OKAY
from hwtLib.avalon.mm_buff import AvalonMmBuff
from hwtLib.handshaked.streamNode import StreamNode


class AvalonMm_to_Axi4(BusBridge):
    """
    Convert AvalonMm to AMBA Axi4 interface

    .. hwt-autodoc::
    """

    def _config(self) -> None:
        AvalonMM._config(self)
        self.ID_WIDTH = Param(1)

    def _declr(self) -> None:
        addClkRstn(self)

        with self._paramsShared():
            self.s = AvalonMM()
            self.m: Axi4 = Axi4()._m()

    def _impl(self) -> None:
        avmm_buff = AvalonMmBuff()
        avmm_buff._updateParamsFrom(self.s)
        avmm_buff.ADDR_BUFF_DEPTH = 1
        avmm_buff.DATA_BUFF_DEPTH = 1
        self.avmm_buff = avmm_buff
        avmm_buff.s(self.s)
        avmm = avmm_buff.m

        axi = self.m

        for a in [axi.ar, axi.aw]:
            a: Axi4_addr
            a.addr(avmm.address)
            a.burst(BURST_INCR)
            a.cache(CACHE_DEFAULT)
            a.lock(LOCK_DEFAULT)
            if self.ID_WIDTH > 0:
                a.id(0)
            if self.MAX_BURST > 1:
                a.len(fitTo(avmm.burstCount - 1, a.len, shrink=False))
            else:
                a.len(0)

            a.prot(PROT_DEFAULT)
            a.qos(QOS_DEFAULT)
            a.size(BYTES_IN_TRANS(self.DATA_WIDTH // 8))

        if self.MAX_BURST > 1:
            w_last_cntr = self._reg("w_last_cntr", avmm.burstCount._dtype, def_val=0)
            w_last_cntr_vld = self._reg("w_last_cntr_vld", def_val=0)

            avmm_addr_hs = (avmm.read | avmm.write, ~avmm.waitRequest)
            StreamNode(
                [avmm_addr_hs, ],
                [axi.ar, axi.aw, axi.w],
                extraConds={
                    axi.ar: avmm.read,
                    axi.aw: avmm.write & axi.w.ready & ~w_last_cntr_vld,
                    axi.w: avmm.write & ((axi.aw.ready & ~w_last_cntr_vld) | w_last_cntr_vld),
                },
                skipWhen={
                    axi.ar:~avmm.read,
                    axi.aw:~avmm.write | w_last_cntr_vld,
                    axi.w:~avmm.write,
                }
            ).sync()

            If(avmm.write & axi.aw.ready & axi.w.ready & ~w_last_cntr_vld,
                w_last_cntr(avmm.burstCount - 2),
                w_last_cntr_vld(avmm.burstCount > 1),
            ).Elif(avmm.write & axi.w.ready & (axi.aw.ready | w_last_cntr_vld),
                If(w_last_cntr != 0,
                   w_last_cntr(w_last_cntr - 1),
                ).Else(
                   w_last_cntr_vld(0),
                )
            )
            If(w_last_cntr_vld,
               axi.w.last(w_last_cntr._eq(0))
            ).Else(
               axi.w.last(avmm.burstCount._eq(1))
            )
        else:
            StreamNode(
                [(avmm.read | avmm.write, ~avmm.waitRequest)],
                [axi.ar, axi.aw, axi.w],
                extraConds={
                    axi.ar: avmm.read,
                    axi.aw: avmm.write & axi.w.ready,
                    axi.w: avmm.write & axi.w.ready,
                },
                skipWhen={
                    axi.ar:~avmm.read,
                    axi.aw:~avmm.write,
                    axi.w:~avmm.write,
                }
            ).sync()

            axi.w.last(1)

        axi.w.data(avmm.writeData)
        axi.w.strb(avmm.byteEnable)

        avmm.readData(axi.r.data)
        avmm.readDataValid(axi.r.valid)
        axi.r.ready(1)

        Switch(axi.b.resp)\
        .Case(RESP_OKAY,
            avmm.response(AVMM_RESP_OKAY),
        ).Case(RESP_EXOKAY,
            avmm.response(AVMM_RESP_OKAY),
        ).Case(RESP_SLVERR,
            avmm.response(RESP_SLAVEERROR),
        ).Case(RESP_DECERR,
            avmm.response(RESP_DECODEERROR),
        ).Default(
            avmm.response(None)
        )
        avmm.writeResponseValid(axi.b.valid)
        axi.b.ready(1)

        propagateClkRstn(self)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = AvalonMm_to_Axi4()
    u.MAX_BURST = 2 ** 7 - 1
    u.DATA_WIDTH = 256
    u.ADDR_WIDTH = 26
    print(to_rtl_str(u))
