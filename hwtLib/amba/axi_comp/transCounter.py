from hwt.code import If, connect
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axiLite_comp.endpoint import AxiLiteEndpoint
from hwtLib.handshaked.streamNode import StreamNode


class AxiTransactionCouter(Unit):
    """
    Counter of beats on axi interface
    write to control register to clear counters

    .. hwt-schematic::
    """
    def __init__(self, axiCls=Axi4):
        self._axiCls = axiCls
        super(AxiTransactionCouter, self).__init__()

    def _config(self):
        self._axiCls._config(self)
        self.CNTRL_DATA_WIDTH = Param(32)
        self.CNTRL_ADDR_WIDTH = Param(32)
        self.CNTR_WIDTH = Param(16)

    def _declr(self):
        assert self.CNTRL_ADDR_WIDTH >= self.CNTR_WIDTH
        addClkRstn(self)
        with self._paramsShared():
            self.master = self._axiCls()._m()
            self.slave = self._axiCls()

        self.cntrl = Axi4Lite()
        mem_space = HStruct(
            (Bits(1), "control"),
            (Bits(32-1), None),
            (Bits(32), "ar"),
            (Bits(32), "aw"),
            (Bits(32), "r"),
            (Bits(32), "w"),
            (Bits(32), "b")
        )
        ep = self.axi_ep = AxiLiteEndpoint(mem_space)
        ep.ADDR_WIDTH = self.CNTRL_ADDR_WIDTH
        ep.DATA_WIDTH = self.CNTRL_DATA_WIDTH
        self.cntrl.ADDR_WIDTH = self.CNTRL_ADDR_WIDTH
        self.cntrl.DATA_WIDTH = self.CNTRL_DATA_WIDTH

    def _impl(self):
        propagateClkRstn(self)
        self.axi_ep.bus(self.cntrl)
        ep = self.axi_ep.decoded
        doClr = ep.control.dout.vld
        ep.control.din(1)
        self.master(self.slave)

        s, m = self.slave, self.master
        for dir_, name in [(1, "ar"), (1, "aw"), (1, "w"), (0, "r"), (0, "b")]:
            sCh = getattr(s, name)
            mCh = getattr(m, name)
            if not dir_:
                sCh, mCh = mCh, sCh

            cntrl = getattr(ep, name)

            ack = StreamNode(masters={sCh}, slaves={mCh}).ack()
            cntr = self._reg("cntr_" + name, Bits(self.CNTR_WIDTH), def_val=0)
            If(doClr,
               cntr(0)
            ).Elif(ack,
               cntr(cntr + 1)
            )
            connect(cntr, cntrl.din, fit=True)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = AxiTransactionCouter()
    print(toRtl(u))
