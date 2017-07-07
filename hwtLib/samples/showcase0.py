from hwt.code import connect, If, Concat
from hwt.hdlObjects.types.bits import Bits
from hwt.interfaces.std import Signal, VectSignal
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwtLib.types.ctypes import uint32_t, int32_t, uint8_t
from hwt.interfaces.utils import addClkRstn
from hwt.serializer.vhdl.serializer import VhdlSerializer
from hwt.serializer.verilog.serializer import VerilogSerializer
from hwt.serializer.systemC.serializer import SystemCSerializer


def foo(condition0, statements, condition1, fallback0, fallback1):
    return If(condition0,
              statements
           ).Elif(condition1,
              fallback0,
           ).Else(
              fallback1
           )


class Showcase0(Unit):
    """
    Every HW component class has to be derived from Unit class (any kind of inheritance supported)
    """
    def __init__(self):
        # constructor can be overloaded but parent one has to be called
        super(Showcase0, self).__init__()

    def _declr(self):
        """
        In this function collecting of public interfaces is performed
        on every attribute assignment. Instances of Interface or Unit are recognized
        by Unit instance and are used as public interface of this unit.

        Direction of interfaces is resolved by access from inside of this unit
        and you do not have to care about it.
        """
        self.a = Signal(dtype=uint32_t)
        self.b = Signal(dtype=int32_t)

        # behavior same as uint32_t (which is Bits(32, signed=False))
        self.c = Signal(dtype=Bits(32))
        # VectSignal is just shortcut for Signal(dtype=Bits(...))
        self.c_sign = VectSignal(32, signed=True)
        self.fitted = VectSignal(16)
        self.contOut = VectSignal(32)

        # this signal will have no driver and it will be considered to be an input
        self.d = VectSignal(32)

        # names of public ports can not be same because they need to accessed from parent
        self.e = Signal()
        self.f = Signal()
        self.g = VectSignal(8)

        # this function just instantiate clk and rstn interface
        # main purpose is to unify names of clock and reset signals
        addClkRstn(self)

        # Unit will not care for object which are not instance of Interface or Unit,
        # other object has to be registered manually
        self.cmp = [Signal() for _ in range(6)]
        self._registerArray("cmp", self.cmp)

        self.h = VectSignal(8)
        self.i = VectSignal(2)
        self.j = VectSignal(8)

    def _impl(self):
        """
        Purpose of this method
        In this method all public interfaces and configuration has been made and they can not be edited.
        """
        a = self.a
        b = self.b

        # ** is overloaded to do assignment
        self.c ** (a + b._convert(a._dtype))

        # width of signals is not same, this would raise TypeError on regular assignment,
        # this behavior can be overriden by calling connect with fit=True
        connect(a, self.fitted, fit=True)

        # every signal/value has _dtype attribute which is parent type
        # most of the types have physical size, bit_lenght returns size of this type in bits
        assert self.a._dtype.bit_length() == 32

        # it is possible to create signal explicitly by calling ._sig
        const_private_signal = self._sig("const_private_signal", dtype=uint32_t, defVal=123)
        self.contOut ** const_private_signal

        # this signal will be optimized out because it has no effect on any output
        # default type is BIT
        self._sig("optimizedOut", dtype=uint32_t, defVal=123)

        # by _reg function usual d-register can be instantiated
        # to be able to use this this unit has to have clock defined (you can force any signal as clock
        # if you call self._cntx._reg directly)
        r = self._reg("r", defVal=0)
        If(~r,  # ~ is negation operator
           # you can directly assign to register and it will assign to its next value
           # (assigned value appears in it in second clk tick)
           r ** self.e
        )
        # again signals has to affect output or they will be optimized out
        self.f ** r

        # instead of and, or, xor use &, |, ^ because they are overridden to do the job
        tmp0 = a[1] & b[1]
        tmp1 = (a[0] ^ b[0]) | a[1]

        # bit concatenation is done by Concat function, python like slicing supported
        self.g ** Concat(tmp0, tmp1, a[6:])

        # comparison operators works as expected
        c = self.cmp
        c[0] ** (a < 4)
        c[1] ** (a > 4)
        c[2] ** (b <= 4)
        c[3] ** (b >= 4)
        c[4] ** (b != 4)
        # except for ==, overriding == would have many unintended consequences in python
        c[5] ** b._eq(4)

        # all statements are just lists of conditional assignments
        statements0 = self.h ** 0
        statements1 = self.h ** 1
        statements2 = self.h ** 2
        statements3 = foo(r, statements0, a[1], statements1, statements2)
        assert len(statements3) == 3
        If(a[2],
            # also when there is not value specified in the branch of dataflow (= in this case there is no else
            # this signal will become latched)
            statements3
        )

        # all statements like Switch, For and others are in hwt.code

        # names of generated signals are patched to avoid collisions
        r0 = self._reg("r", Bits(2), defVal=0)
        r1 = self._reg("r", Bits(2), defVal=0)

        r0 ** self.i
        r1 ** r0

        # type of signal can be array as well, this allow to create memories like BRAM...
        # mem will be synchronous ROM in this case
        mem = self._sig("mem", uint8_t[4], defVal=[i for i in range(4)])

        If(self.clk._onRisingEdge(),
           self.j ** mem[r1]
        )


if __name__ == "__main__":  # alias python main function
    from hwt.synthesizer.shortcuts import toRtl
    # new instance has to be created everytime because toRtl is modifies the unit
    print(toRtl(Showcase0(), serializer=VhdlSerializer))
    print(toRtl(Showcase0(), serializer=VerilogSerializer))
    print(toRtl(Showcase0(), serializer=SystemCSerializer))
