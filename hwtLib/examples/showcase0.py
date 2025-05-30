#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The class :class:`~.Showcase0` can be converted to various target formats as
can be seen in "main" of this file.

There are several examples:

.. literalinclude:: /../hwtLib/examples/showcase0.v
   :language: verilog
   :caption: Verilog Std IEEE 1364-2001
   :linenos:

.. literalinclude:: /../hwtLib/examples/showcase0.vhd
   :language: vhdl
   :caption: VHDL IEEE Std 1076-2002
   :linenos:

.. literalinclude:: /../hwtLib/examples/showcase0.cpp
   :language: cpp
   :caption: SystemC IEEE Std 1666-2011
   :linenos:

.. literalinclude:: /../hwtLib/examples/showcase0.hwt.py
   :language: python
   :caption: HWT :class:`hwt.hwModule.HwModule` class definition
   :linenos:
"""

from hwt.code import If, Concat, Switch
from hwt.hObjList import HObjList
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOSignal, HwIOVectSignal
from hwt.hwIOs.utils import addClkRstn
from hwt.hwModule import HwModule
from hwt.pyUtils.typingFuture import override
from hwtLib.types.ctypes import uint32_t, int32_t, uint8_t, int8_t


def foo(condition0, statements, condition1, fallback0, fallback1):
    """
    Python functions used as macro
    """
    return If(condition0,
              statements
           ).Elif(condition1,
              fallback0,
           ).Else(
              fallback1
           )


class Showcase0(HwModule):
    """
    Every HW component class has to be derived from :class:`hwt.hwModule.HwModule` class

    .. hwt-autodoc::
    """
    # note that class doc string is also converted to generated HDL

    def __init__(self):
        # constructor can be overloaded but parent one has to be called
        super(Showcase0, self).__init__()

    @override
    def hwDeclr(self):
        """
        In this function collecting of public interfaces is performed
        on every attribute assignment. Instances of Interface or :class:`hwt.hwModule.HwModule` are recognized
        by :class:`hwt.hwModule.HwModule` instance and are used as public interface of this unit.

        Master interfaces are marked by "._m()", meaning of master direction
        is specified in HwIO class. For simple signal master direction means output.
        """
        self.a = HwIOSignal(dtype=uint32_t)
        self.b = HwIOSignal(dtype=int32_t)

        # behavior same as uint32_t (which is HBits(32, signed=False))
        self.c = HwIOSignal(dtype=HBits(32))._m()
        # VectSignal is just shortcut for Signal(dtype=HBits(...))
        self.fitted = HwIOVectSignal(16)._m()
        self.contOut = HwIOVectSignal(32)._m()

        # this signal will have no driver and it will be considered to be an input
        self.d = HwIOVectSignal(32)

        # names of public ports can not be same because they need to be accessible from parent
        self.e = HwIOSignal()
        self.f = HwIOSignal()._m()
        self.g = HwIOVectSignal(8)._m()

        # this function just instantiate clk and rstn interface
        # main purpose is to unify names of clock and reset signals
        addClkRstn(self)

        # HObjList is just regular list, it is used to tell HwModule/Interface
        # to look inside while searching for nested Interface/HwModule instances
        self.cmp = HObjList(
            HwIOSignal() for _ in range(6)
        )._m()

        self.h = HwIOVectSignal(8)._m()
        self.i = HwIOVectSignal(2)
        self.j = HwIOVectSignal(8)._m()

        # collision with hdl keywords are automatically resolved and fixed
        # as well as case sensitivity care and other collisions in target HDL
        self.out = HwIOSignal()._m()
        self.output = HwIOSignal()._m()
        self.sc_signal = HwIOVectSignal(8)._m()

        self.k = HwIOVectSignal(32)._m()

    @override
    def hwImpl(self):
        """
        Purpose of this method
        In this method all public interfaces and configuration
        has been made and they can not be edited.
        """
        # create local variable to make code shorter
        a = self.a
        b = self.b

        # "call" is overloaded to do assignment
        # it means c = a + b in target HDL
        # type conversion is can be done by _auto_cast or _reinterpret_cast method call
        self.c(a + b._auto_cast(a._dtype))

        # width of signals is not same, this would raise TypeError on regular assignment,
        # this behavior can be overridden by calling connect with fit=True
        self.fitted(a, fit=True)

        # every signal/value has _dtype attribute which is parent type
        # most of the types have physical size, bit_lenght returns size of this type in bits
        assert self.a._dtype.bit_length() == 32

        # it is possible to create signal explicitly by calling ._sig method
        # result of every operator is signal
        const_private_signal = self._sig("const_private_signal",
                                         dtype=uint32_t, def_val=123)
        self.contOut(const_private_signal)

        # this signal will be optimized out because it has no effect on any output
        # self.d will remain because it is part of interface
        self._sig("optimizedOut", dtype=uint32_t, def_val=123)

        # by _reg function usual d-register can be instantiated
        # to be able to use this this unit has to have clock defined
        # (you can force any signal as clock if you call self._rtlCtx._reg directly)
        # default type is BIT
        r = self._reg("r", def_val=0)

        # HDL If statement is object
        # ~ is negation operator
        If(~r,
           # you can directly assign to register and it will assign to its next value
           # (assigned value appears in it in second clk tick)
           r(self.e)
        )

        # again signals has to affect output or they will be optimized out
        self.f(r)

        # instead of and, or, xor use &, |, ^ because they are overridden to do the job
        tmp0 = a[1] & b[1]
        tmp1 = (a[0] ^ b[0]) | a[1]

        # bit concatenation is done by Concat function, python like slicing supported
        self.g(Concat(tmp0, tmp1, a[6:]))

        # results of comparison operators assigned to bits of cmp signal
        cmp = self.cmp
        cmp[0](a < 4)
        cmp[1](a > 4)
        cmp[2](b <= 4)
        cmp[3](b >= 4)
        cmp[4](b != 4)
        # _eq() is used as ==,
        # overriding == would have many unintended consequences in python
        # (it would make all signals unhashable)
        cmp[5](b._eq(4))

        h = self.h
        # all statements are just objects
        statements0 = h(0)
        statements1 = h(1)
        statements2 = h(2)
        statements3 = foo(r, statements0, a[1], statements1, statements2)
        assert isinstance(statements3, If)
        If(a[2],
            # also when there is not value specified in the branch of dataflow
            # (in this case there is missing else branch) this signal will become latched
            statements3
        )

        # all statements like If, Switch, For and others are in hwt.code

        # names of generated signals are patched to avoid collisions automatically
        r0 = self._reg("r", HBits(2), def_val=0)
        r1 = self._reg("r", HBits(2), def_val=0)
        # all processes with the similar statement structure are merged to reduce HDL code size
        # in this case processes for registers are merged into one

        r0(self.i)
        r1(r0)

        # type of signal can be array as well, this allow to create memories like BRAM...
        # ROM will be synchronous ROM in this case
        rom = self._sig("rom", uint8_t[4], def_val=[i for i in range(4)])

        If(self.clk._onRisingEdge(),
           self.j(rom[r1])
        )

        self.out(0)
        # None is converted to value with zero validity mask
        # same as self.output._dtype.from_py(0, vld_mask=0)
        self.output(None)

        # statements are code-generator frendly
        stm = \
        Switch(a).Case(1,
            self.sc_signal(0)
        ).Case(2,
           self.sc_signal(1)
        )
        compileTimeCondition = True

        if compileTimeCondition:
            stm.Case(3,
               self.sc_signal(3)
            ).Default(
               self.sc_signal(4)
            )

        # ram working on falling edge of clk
        # note that rams are usually working on rising edge
        fRam = self._sig("fallingEdgeRam", int8_t[4])
        If(self.clk._onFallingEdge(),
           # fit can extend signal and also shrink it (sext/zext based on sing of the type)
           fRam[r1](a, fit=True), # trunc
           self.k(fRam[r1]._unsigned(), fit=True) # zext
        )


if __name__ == "__main__":  # alias python main function
    from pprint import pprint

    from hwt.synth import to_rtl_str
    from hwt.serializer.hwt import HwtSerializer
    from hwt.serializer.vhdl import Vhdl2008Serializer
    from hwt.serializer.verilog import VerilogSerializer
    from hwt.serializer.systemC import SystemCSerializer

    from hwt.serializer.resourceAnalyzer.analyzer import ResourceAnalyzer
    from hwt.synth import synthesised

    # * new instance has to be created every time because to_rtl_str modifies the unit
    # * serializers are using templates which can be customized
    # serialized code is trying to be human and git friendly
    print(to_rtl_str(Showcase0(), serializer_cls=HwtSerializer))
    print(to_rtl_str(Showcase0(), serializer_cls=Vhdl2008Serializer))
    print(to_rtl_str(Showcase0(), serializer_cls=VerilogSerializer))
    print(to_rtl_str(Showcase0(), serializer_cls=SystemCSerializer))

    m = Showcase0()
    ra = ResourceAnalyzer()
    synthesised(m)
    ra.visit_HwModule(m)
    pprint(ra.report())
