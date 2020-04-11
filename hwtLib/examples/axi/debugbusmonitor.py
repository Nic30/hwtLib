from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.unit import Unit
from hwtLib.abstract.debug_bus_monitor import DebugBusMonitor
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axiLite_comp.endpoint import AxiLiteEndpoint
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.reg import AxiSReg


class DebugBusMonitorExampleAxi(Unit):
    """
    """
    def _config(self):
        Axi4Lite._config(self)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.s = Axi4Lite()
        self.din0 = AxiStream()
        self.dout0 = AxiStream()._m()
        self.reg = AxiSReg()
        self.din1 = AxiStream()
        self.dout1 = AxiStream()._m()

    def _impl(self):
        self.dout0(self.din0)
        self.reg.dataIn(self.din1)
        self.dout1(self.reg.dataOut)

        db = DebugBusMonitor(Axi4Lite, AxiLiteEndpoint)
        for i in [self.din0,
                  self.dout0, self.din1,
                  self.reg.dataIn, self.reg.dataOut,
                  self.dout1,
                  ]:
            db.register(i)
    
        with self._paramsShared():
            self.db = db
        db.s(self.s)
        db.apply_connections()

        propagateClkRstn(self)


if __name__ == '__main__':
    from hwt.synthesizer.utils import toRtl
    u = DebugBusMonitorExampleAxi()
    print(toRtl(u))
