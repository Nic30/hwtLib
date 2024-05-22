from hwt.hwIOs.std import HwIOSignal
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwModule import HwModule
from hwtLib.examples.simpleHwModuleWithNonDirectIntConncetion import SimpleHwModuleWithNonDirectIntConncetion


class AccessingSubunitInternalIntf(HwModule):
    """
    Example of error from accessing a internal interface of subunit
    """

    def _declr(self):
        addClkRstn(self)
        self.submodule0 = SimpleHwModuleWithNonDirectIntConncetion()
        self.a0 = HwIOSignal()
        self.b0 = HwIOSignal()._m()
        self.c0 = HwIOSignal()._m()

    def _impl(self):
        propagateClkRstn(self)
        m = self.submodule0
        m.a(self.a0)
        self.c0(m.b)
        self.b0(m.c)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    
    m = AccessingSubunitInternalIntf()
    print(to_rtl_str(m))
