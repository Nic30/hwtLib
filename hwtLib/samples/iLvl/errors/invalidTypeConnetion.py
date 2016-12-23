from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.interfaces.std import VectSignal


class InvalidTypeConnetion(Unit):
    def _declr(self):
        self.a = VectSignal(32)
        self.b = VectSignal(64)
    
    def _impl(self):
        # missing fitTo()
        self.a ** self.b


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = InvalidTypeConnetion()
    # expecting hwt.synthesizer.exceptions.TypeConversionErr
    print(toRtl(u))        