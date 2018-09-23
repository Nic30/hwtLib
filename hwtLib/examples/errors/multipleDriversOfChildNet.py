from hwt.synthesizer.unit import Unit
from hwt.interfaces.std import Handshaked


class ExampleChild(Unit):
    def _declr(self):
        self.c = Handshaked()
        self.d = Handshaked()._m()

    def _impl(self):
        self.d(self.c)


class MultipleDriversOfChildNet(Unit):
    def _declr(self):
        self.a = Handshaked()
        self.b = Handshaked()._m()

        self.ch = ExampleChild()

    def _impl(self):
        # interface directions in collision
        self.ch.d(self.a)
        self.ch.c.data(1)
        self.ch.c.vld(1)
        self.b(self.ch.c)


class MultipleDriversOfChildNet2(MultipleDriversOfChildNet):
    def _impl(self):
        self.ch.c(self.a)
        self.b(self.ch.d)
        # another colliding driver for b.vld
        self.b.vld(1)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = MultipleDriversOfChildNet()
    # hwt.serializer.exceptions.SerializerException
    print(toRtl(u))

