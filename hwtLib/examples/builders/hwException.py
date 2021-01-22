#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.unit import Unit
from hwtLib.abstract.hwExceptionCtx import HwExceptionCtx, InHwError
from hwtLib.handshaked.streamNode import StreamNode


class ExampleHwException0(InHwError):
    """
    An example of InHwError error.
    This object behaves as a regular python exception and can be used in
    :class:`hwtLib.abstract.hwExceptionCtx.HwExceptionCtx` functions
    which are construction an exception raising/catching logic.
    """
    pass


class ExampleHwException1(InHwError):
    pass


class HwExceptionRaise(Unit):
    """
    An example of :class:`hwtLib.abstract.hwExceptionCtx.HwExceptionCtx` usage.

    (a handshaked wire which will stall until exception is handled, however only exception caused by value 1
     has an interface for handlig and thus all other exceptions will cause stall until reset)

    .. hwt-autodoc:
    """

    def _declr(self):
        # clock and reset is required because the status
        # of the exception handling needs to be stored in register
        addClkRstn(self)
        self.dataIn = Handshaked()
        self.dataOut = Handshaked()._m()


    def _impl(self):
        err0 = self._sig("exception_handling_in_progress0")
        err0_detected = self._sig("exception_detected0")
        err1 = self._sig("exception_handling_in_progress1")
        err1_detected = self._sig("exception_detected1")
        din = self.dataIn
        errCtx = HwExceptionCtx(self)
        If(din.vld,
            If(din.data._eq(0),
                # HwExceptionCtx.hw_raise creates an io and status flag for an exception instance
                # the exception can have hardware parameters (first argument) which are translated
                # to an interface as well and the python arguments (rest of the arguments)
                # :note: exception raising involves only synchronization signal routing, it does not copy the
                #     arguments of the exception and thus they needs to stay constant duing exception handling
                # :note: pending_flag and raising_flag can be used to get the signal which signalizes that the exception is pending
                #     and is not handled yet.
                # :note: The raise of error does not affect the rest of the code, in order to do so we
                #     need to use raising_flag/pending_flag, in this case we used it to stall dataIn/dataOut
                errCtx.hw_raise(
                    # first argument is passed to hardware interface responsible for
                    # exception handling, the rest of arguments are standard Python Exception args/kwargs
                    ExampleHwException0((din.data,), "Example raise 1"),
                    raising_flag=err0_detected,
                    pending_flag=err0,
                )
            ).Elif(din.data._eq(1),
                errCtx.hw_raise(
                    ExampleHwException1((), "Example raise 2"),
                    raising_flag=err1_detected,
                    pending_flag=err1
                )
            )
        )
        dout = self.dataOut
        If(err0 | err0_detected | err1 | err1_detected,
           dout.data(None)
        ).Else(
           dout.data(din.data)
        )

        # dissable input if any error is beeing handled
        # do not propagate values which are rising an error on output
        StreamNode(
            [din], [dout],
            extraConds={
                din: ~(err0 | err1), # stall while an error is beeing processed
                dout: ~(err0 | err0_detected | err1 | err1_detected)}, # stall if errror appeared or error is beeing processed
            skipWhen={
                dout: err0_detected | err1_detected, # drop if error value is detected
            }
        ).sync()


class HwExceptionCatch(Unit):
    """
    An example of :class:`hwtLib.abstract.hwExceptionCtx.HwExceptionCtx` usage.

    (a handshaked wire which will stall until reset if 0,1 or 2 appears in data,
     only exception caused by value 1 can be handled)


    .. hwt-autodoc:
    """

    def _declr(self):
        HwExceptionRaise._declr(self)

    def _impl(self):
        c = self.c = HwExceptionRaise()
        err0 = self._sig("exception_handling_in_progress0")
        err0_detected = self._sig("exception_detected0")
        din = self.dataIn

        # dissable input if error is beeing handled
        If(err0 | err0_detected,
            c.dataIn.data(None)
        ).Else(
            c.dataIn.data(din.data)
        )

        # dissable input if error is beeing handled
        # do not propagate input values which are rising an error on subcomponent c input
        StreamNode(
            [din], [c.dataIn],
            extraConds={
                din: ~err0, # stall while an error is beeing processed
                c.dataIn: ~(err0 | err0_detected)}, # stall if errror appeared or error is beeing processed
            skipWhen={
                c.dataIn: err0_detected, # drop if error value is detected
            }
        ).sync()

        self.dataOut(c.dataOut)
        errCtx = HwExceptionCtx(self)
        If(din.vld,
            If(din.data._eq(2),
                errCtx.hw_raise(
                    ExampleHwException0((din.data,), "Example raise 1"),
                    raising_flag=err0_detected,
                    pending_flag=err0)
            )
        )

        # HwExceptionCtx.hw_catch catches all exceptions of specified class from current scope
        # and all children components if the exception was not catched yet
        for e_intf in errCtx.hw_catch(ExampleHwException0):
            # never handle and thus stall this component until hard reset
            e_intf.rd(0)
            # those exception handle interfaces which are left with undriven rd
            # are considered to be unhadled and will be returned also in another catch
            # of this exception

        # HwExceptionCtx.propagate() propagates all uncatched exceptions from all children
        # (unahdled exceptions from self are propagated automatically)
        # :note: If there is some unhandled exception and the propagate is not called
        #     it will result in the driver error of the exception interface
        errCtx.propagate()
        propagateClkRstn(self)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = HwExceptionCatch()
    print(to_rtl_str(u))
