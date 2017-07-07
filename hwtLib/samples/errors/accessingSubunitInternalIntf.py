from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwtLib.samples.simpleWithNonDirectIntConncetion import SimpleWithNonDirectIntConncetion


class AccessingSubunitInternalIntf(Unit):
    def _declr(self):
        addClkRstn(self)
        self.subunit0 = SimpleWithNonDirectIntConncetion()
        self.a0 = Signal()
        self.b0 = Signal()
        self.c0 = Signal()


    def _impl(self):
        propagateClkRstn(self)
        u = self.subunit0
        u.a ** self.a0
        self.c0 ** u.b
        self.b0 ** u.c