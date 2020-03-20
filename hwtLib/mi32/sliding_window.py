from hwtLib.abstract.busBridge import BusBridge
from hwtLib.mi32.intf import Mi32
from hwt.synthesizer.param import Param
from hwt.interfaces.utils import addClkRstn
from hwt.code import isPow2, connect, If


class Mi32SlidingWindow(BusBridge):
    """
    Address space window + offset register which allows to address bigger
    address space than available on input interface due size of its address signal

    :note: address_space = HStruct(
        (Bits(8)[WINDOW_SIZE], "window"),
        (Bits(DATA_WIDTH),     "offset"),
        )
    :note: offset is write only
    """

    def _config(self):
        Mi32._config(self)
        self.M_ADDR_WIDTH = Param(self.ADDR_WIDTH)
        self.WINDOW_SIZE = Param(4096)

    def _declr(self):
        assert isPow2(self.WINDOW_SIZE)
        addClkRstn(self)
        with self._paramsShared(exclude=({"ADDR_WIDTH"}, {})):
            self.m = Mi32()._m()
            self.m.ADDR_WIDTH = self.M_ADDR_WIDTH
            self.s = Mi32()
            self.s.ADDR_WIDTH = self.ADDR_WIDTH

    def _impl(self):
        OFFSET_REG_ADDR = self.WINDOW_SIZE
        m, s = self.s, self.m
        offset_en = m.addr._eq(OFFSET_REG_ADDR)
        offset = self._reg("offset", s.addr._dtype, def_val=0)
        connect(m, s, exclude={m.addr, m.wr, m.ardy})
        s.addr(offset + m.addr._reinterpret_cast(offset._dtype))
        s.wr(m.wr & ~offset_en)
        If(offset_en & m.wr,
           connect(m.dwr, offset, fit=True)
        )
        m.ardy(s.ardy | (m.wr & offset_en))


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl

    u = Mi32SlidingWindow()
    u.ADDR_WIDTH = 16
    u.M_ADDR_WIDTH = 32
    print(toRtl(u))
