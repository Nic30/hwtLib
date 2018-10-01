from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.unit import Unit
from hwtLib.examples.simpleWithNonDirectIntConncetion import SimpleWithNonDirectIntConncetion


class AccessingSubunitInternalIntf(Unit):
    """
    Example of error from accessing a internal interface of subunit
    """
    
    def _declr(self):
        addClkRstn(self)
        self.subunit0 = SimpleWithNonDirectIntConncetion()
        self.a0 = Signal()
        self.b0 = Signal()._m()
        self.c0 = Signal()._m()

    def _impl(self):
        propagateClkRstn(self)
        u = self.subunit0
        u.a(self.a0)
        self.c0(u.b)
        self.b0(u.c)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = AccessingSubunitInternalIntf()
    print(toRtl(u))