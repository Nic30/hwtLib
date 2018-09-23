from hwt.synthesizer.unit import Unit
from hwt.interfaces.std import VectSignal


class InvalidTypeConnetion(Unit):
    def _declr(self):
        self.a = VectSignal(32)._m()
        self.b = VectSignal(64)

    def _impl(self):
        # wrong size can be overriden by connect(src, dst, fit=True)
        self.a(self.b)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = InvalidTypeConnetion()
    # expecting hwt.synthesizer.exceptions.TypeConversionErr
    print(toRtl(u))
