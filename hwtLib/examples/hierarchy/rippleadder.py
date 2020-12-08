#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Concat
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Signal, VectSignal
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit


@serializeParamsUniq
class FullAdder(Unit):
    """
    .. hwt-autodoc::
    """

    def _declr(self):
        self.a = Signal()
        self.b = Signal()
        self.ci = Signal()
        self.s = Signal()._m()
        self.co = Signal()._m()

    def _impl(self):
        # [note] it is usually better to copy commonly used self properties because it makes code shorter
        a, b, ci = self.a, self.b, self.ci

        self.s(a ^ b ^ ci)
        self.co(a & b | a & ci | b & ci)


# [wrong] the class is missing serializeParamsUniq decorator,
# this means taht it will be serialized as a new module/entity for each instance, but it is not required
class RippleAdder0(Unit):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        # [possible improvement] you can specify the type directly, this may be more futureproof
        # in this case we could also controll if the data type should be signed/unsigned
        self.p_wordlength = Param(4)

    def _declr(self):
        self.ci = Signal()
        self.a = VectSignal(self.p_wordlength)
        self.b = VectSignal(self.p_wordlength)
        self.s = VectSignal(self.p_wordlength)._m()
        self.co = Signal()._m()

        # [wrong] manually instantiated child components (it is better to use HObjList)
        self.fa0 = FullAdder()
        self.fa1 = FullAdder()
        self.fa2 = FullAdder()
        self.fa3 = FullAdder()

    def _impl(self):
        # [wrong] VectSignal is an Interface sub-class, it is ment to be used for IO of the component
        # it works but it has significant limitations, you should use self._sig() wihich handles name collisions
        # and has more confort API for clock/reset/default value specifications
        self.c = VectSignal(self.p_wordlength + 1)
        self.c[0](self.ci)
        self.co(self.c[self.p_wordlength])

        # [wrong] manually unrolled/hardcoded for loop 
        u_fa0 = self.fa0
        u_fa1 = self.fa1
        u_fa2 = self.fa2
        u_fa3 = self.fa3

        u_fa0.a(self.a[0])
        u_fa1.a(self.a[1])
        u_fa2.a(self.a[2])
        u_fa3.a(self.a[3])

        u_fa0.b(self.a[0])
        u_fa1.b(self.a[1])
        u_fa2.b(self.a[2])
        u_fa3.b(self.a[3])

        # [wrong] Why use bits of "c" singal if we can connect ports directly
        u_fa0.ci(self.c[0])

        self.c[1](u_fa0.co)
        u_fa1.ci(self.c[1])

        self.c[2](u_fa0.co)
        u_fa2.ci(self.c[2])

        self.c[3](u_fa0.co)
        u_fa3.ci(self.c[3])

        self.c[4](u_fa0.co)
        
        # [wrong] why to assing each bit separately if we can assing it all it once from concat of fa.s io
        self.s[0](u_fa0.s)
        self.s[1](u_fa1.s)
        self.s[2](u_fa2.s)
        self.s[3](u_fa3.s)


@serializeParamsUniq
class RippleAdder1(Unit):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.p_wordlength = Param(4)

    def _declr(self):
        self.ci = Signal()
        self.a = VectSignal(self.p_wordlength)
        self.b = VectSignal(self.p_wordlength)
        self.s = VectSignal(self.p_wordlength)._m()
        self.co = Signal()._m()

        self.fa = HObjList([
           FullAdder() for _ in range(self.p_wordlength)
        ])

    def _impl(self):
        c = self._sig("c", Bits(self.p_wordlength + 1))

        c[0](self.ci)
        for bitidx, fa in enumerate(self.fa):
            fa.a(self.a[bitidx])
            fa.b(self.b[bitidx])
            fa.ci(c[bitidx])
            # not like in verilog, port is just another signal, direction of assignment does matter
            c[bitidx + 1](fa.co)
            self.s[bitidx](fa.s)
        self.co(c[self.p_wordlength])


@serializeParamsUniq
class RippleAdder2(Unit):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.p_wordlength = Param(4)

    def _declr(self):
        self.ci = Signal()
        # [possible improvement] you can use io = lambda : VectSignal(self.p_wordlength) as macro
        # so you do not have to repeat same code 
        self.a = VectSignal(self.p_wordlength)
        self.b = VectSignal(self.p_wordlength)
        self.s = VectSignal(self.p_wordlength)._m()
        self.co = Signal()._m()

    def _impl(self):
        # [wrong] it is useless to use an extra signal to connect ports,  because it can be connected directly
        c = self._sig("c", Bits(self.p_wordlength + 1))

        lci = [FullAdder()  for _ in range(self.p_wordlength)]
        self.fa = HObjList(lci)

        c[0](self.ci)
        for bitIdx in range(self.p_wordlength):
            # [wrong] python iteration using range and indexing is slower than using enumerate()
            fa = lci[bitIdx]

            fa.a(self.a[bitIdx])
            fa.b(self.b[bitIdx])
            fa.ci(c[bitIdx])
            # not like in verilog, port is just another signal, direction of assignment does matter
            c[bitIdx + 1](fa.co)
            self.s[bitIdx](fa.s)

        self.co(c[self.p_wordlength])


@serializeParamsUniq
class RippleAdder3(Unit):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.p_wordlength = Param(4)

    def _declr(self):
        self.ci = Signal()
        self.a = VectSignal(self.p_wordlength)
        self.b = VectSignal(self.p_wordlength)
        self.s = VectSignal(self.p_wordlength)._m()
        self.co = Signal()._m()

    def _impl(self):
        carry = self.ci

        # [note] HObjList can be restered with or without items, however we need it in adwance because we
        # need registered FullAdder adder instances, because we need it's IO
        fa_list = self.fa = HObjList()
        for a, b in zip(self.a, self.b):
            # [note] componnets do not have to be declared in _declr(), but it is better
            # because the configuration of component can be still modified
            # after _declr() in _impl() the configuration of component is locked imediately after registration
            fa = FullAdder()
            # [note] the component have to be registered in order to spot the IO
            # the registration is done by assining to a property ot his object e.g. self.fa0 = fa
            # or by adding to some already registered object, in this case HObjList instance
            fa_list.append(fa)
            fa.a(a)
            fa.b(b)
            fa.ci(carry)
            carry = fa.co

        # [note] we have to reverse because of downto indexing
        self.s(Concat(*reversed([fa.s for fa in fa_list])))
        self.co(carry)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u1 = RippleAdder1()
    u2 = RippleAdder2()
    u3 = RippleAdder3()
    from hwt.serializer.verilog import VerilogSerializer

    print(to_rtl_str(u1, serializer_cls=VerilogSerializer))
    print(to_rtl_str(u2, serializer_cls=VerilogSerializer))
    print(to_rtl_str(u3, serializer_cls=VerilogSerializer))
