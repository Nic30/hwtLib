from hwt.synthesizer.interfaceLevel.unit import Unit
from hwtLib.amba.axis import AxiStream


class UncosistentIntfDirection(Unit):
    def _declr(self):
        self.a = AxiStream()
    
    def _impl(self):
        # missing drivers of self.a
        pass


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = UncosistentIntfDirection()
    # expecting hwt.synthesizer.exceptions.IntfLvlConfErr
    print(toRtl(u))        