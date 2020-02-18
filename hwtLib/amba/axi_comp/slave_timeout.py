from hwt.code import log2ceil, If
from hwt.hdl.types.bits import Bits
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.param import Param
from hwtLib.abstract.busBridge import BusBridge
from hwtLib.amba.constants import RESP_SLVERR


class AxiSlaveTimeout(BusBridge):
    """
    Component witch has internal timeout for r/b channel and responds
    with the error code if the slave does not respond in specified time

    :note: blocks the overlapping transactions, it allows only
        a single pedning transaction per type
    """

    def __init__(self, intfCls):
        self.intfCls = intfCls
        super(AxiSlaveTimeout, self).__init__()

    def _config(self):
        self.TIMEOUT = Param(4096)
        self.intfCls._config(self)

    def _declr(self):
        addClkRstn(self)
        self.INTF_CLS = Param(self.intfCls)
        with self._paramsShared():
            self.m = self.intfCls()
            self.s = self.intfCls()._m()

    def _impl(self):
        timer_t = Bits(log2ceil(self.TIMEOUT - 1))
        TIMER_MAX = self.TIMEOUT - 1
        m, s = self.m, self.s
        s.aw(m.aw)
        s.ar(m.ar)
        s.w(m.w)

        r_pending = self._reg("r_pending", def_val=0)
        r_timer = self._reg("timeout_timer_r", timer_t, def_val=TIMER_MAX)
        r_id = self._reg("r_id", m.r.id._dtype)
        If(r_pending,
            r_timer(r_timer - 1),
            If(r_timer._eq(0),
               r_pending(0)
            )
        ).Elif(m.ar.valid & s.ar.ready,
            r_pending(~m.r.valid),
            r_timer(TIMER_MAX),
            r_id(m.ar.id),
        )

        If(r_pending & r_timer._eq(0),
           m.r.valid(1),
           m.r.id(r_id),
           m.r.resp(RESP_SLVERR),
           s.r.ready(1),
        ).Else(
            m.r(s.r)
        )

        b_pending = self._reg("b_pending", def_val=0)
        # b_timer_rst = self._sig("timeout_timer_b_rst")
        b_timer = self._reg("timeout_timer_b", timer_t, def_val=TIMER_MAX)
        b_id = self._reg("b_id", m.aw.id._dtype)
        If(m.aw.valid & s.aw.ready,
           b_id(m.aw.id),
        )
        If(b_pending,
            b_timer(b_timer - 1),
            If(b_timer._eq(0),
               b_pending(0)
            )
        ).Elif(m.w.valid & s.w.ready & m.w.last,
           b_pending(~s.b.valid),
           b_timer(TIMER_MAX),
        )
        If(b_pending & b_timer._eq(0),
           m.b.valid(1),
           m.b.id(b_id),
           m.b.resp(RESP_SLVERR),
           s.b.ready(1),
        ).Else(
            m.b(s.b)
        )

if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    from hwtLib.amba.axi4 import Axi4

    u = AxiSlaveTimeout(Axi4)
    print(toRtl(u))
