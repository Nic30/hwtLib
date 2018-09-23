from hwt.synthesizer.unit import Unit
from hwtLib.amba.axis import AxiStream


class InconsistentIntfDirection(Unit):
    def _declr(self):
        self.a = AxiStream()._m()

    def _impl(self):
        # missing drivers of self.a
        pass


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = InconsistentIntfDirection()
    # expecting hwt.synthesizer.exceptions.IntfLvlConfErr
    print(toRtl(u))
