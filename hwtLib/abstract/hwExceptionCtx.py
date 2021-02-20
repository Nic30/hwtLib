from collections import deque
from typing import Type, List, Tuple, Optional, Union

from hwt.code import If
from hwt.interfaces.std import HandshakeSync
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.interfaceLevel.interfaceUtils.utils import walkPhysInterfaces
from hwt.synthesizer.unit import Unit
from hwtLib.abstract.componentBuilder import AbstractComponentBuilder
from hwtLib.abstract.debug_bus_monitor import monitor_of, connect_to_MonitorIntf
from ipCorePackager.constants import DIRECTION, INTF_DIRECTION
from hwt.synthesizer.rtlLevel.mainBases import RtlSignalBase


class InHwError(Exception):
    """
    A base class for exceptions which are translated to hardware
    and handle in runtime of the hardware.

    :ivar Deque[Unit] hw_traceback: traceback
    """

    def __init__(self, hw_args=None, *args, **kwargs):
        super(InHwError, self).__init__(*args, **kwargs)
        self.hw_traceback = deque()
        if hw_args is None:
            hw_args = ()
        else:
            assert isinstance(hw_args, (tuple, list))
        self.hw_args = hw_args


class ExceptionHandleInterface(HandshakeSync):

    def __init__(self, exception:InHwError, masterDir=DIRECTION.OUT,
                 loadConfig=True):
        HandshakeSync.__init__(self, masterDir=masterDir, loadConfig=loadConfig)
        self._exception = exception

    def _declr(self):
        HandshakeSync._declr(self)
        args = HObjList()
        for a in self._exception.hw_args:
            _a = monitor_of(a)
            args.append(_a)
        self.args = args

    def __copy__(self):
        return self.__class__(self._exception)


class HwExceptionCtx():
    """
    An object which handles hardware exceptions.

    :attention: exception handling requires a clock and reset signal to be present on parent
        :class:`hwt.synthesizer.unit.Unit` instance.
    """

    def __init__(self, parent: Unit, name="raise"):
        self.parent = parent
        self.compId = 0
        self.catch_instances = []
        self.name = name

    def _Unit_registerPublicIntfInImpl(self, intf, name):
        p = self.parent
        p._registerInterface(name, intf, isPrivate=False)
        p._loadInterface(intf, True)
        intf._signalsForInterface(
            p._ctx, p._ctx.interfaces, p._store_manager.name_scope,
            reverse_dir=True)

    def _Unit_makePublicIntfPrivateInImpl(self, intf):
        parent_u = intf._parent
        while not isinstance(parent_u, Unit):
            parent_u = parent_u._parent

        parent_u._interfaces.remove(intf)
        parent_u._private_interfaces.append(intf)

        for s in walkPhysInterfaces(intf):
            if s._direction == INTF_DIRECTION.SLAVE:
                ep = s._sig.endpoints
                ep.remove(s._hdl_port)

            elif s._direction == INTF_DIRECTION.MASTER:
                dr = s._sig.drivers
                dr.remove(s._hdl_port)
            else:
                raise ValueError(s._direction)

            s._sig.ctx.interfaces.pop(s._sig)
            self.parent._ctx.ent.ports.remove(s._hdl_port)
            s._hdl_port = None
            s._isExtern = False

    def hw_raise(self, exception: InHwError,
                 pending_flag:Optional[RtlSignalBase]=None,
                 raising_flag:Optional[RtlSignalBase]=None):
        """
        Construct a logic to raise an exception in generated hardware.
        This creates a flag and IO for exception handling status.

        :param pending_flag: An optional flag which should be set to 1 if exception was raised
            in some previous clock cycle an it has not beed catched yet.
        :param raising_flag: An optional flag which should be set to 1 if exception exception is
            beeing raised in this clock cycle.
        :attention: The arguments specified in the exception has to remain stable until
            the excetion is handled.
        :returns: An expression which triggers the exception handling.
        """
        assert isinstance(exception, InHwError)
        err_name = exception.__class__.__name__
        p = self.parent

        # add a raise interace in impl phase of the Unit instance
        raise_intf = ExceptionHandleInterface(exception)._m()
        self._Unit_registerPublicIntfInImpl(
            raise_intf,
            AbstractComponentBuilder._findSuitableName(self, err_name)
        )
        object.__setattr__(p, raise_intf._name, raise_intf)

        # create a flag which means that the error is waiting
        err_pending = p._reg(f"{self.name:s}_{err_name:s}_pending", def_val=0)
        if pending_flag is not None:
            pending_flag(err_pending)

        If(err_pending,
           err_pending(~raise_intf.rd),
        ).Else(
           err_pending(raise_intf.vld & ~raise_intf.rd),
        )
        raise_intf.vld._sig._nop_val = raise_intf.vld._sig._dtype.from_py(0)
        if exception.hw_args:
            for a_src, a_dst in zip(exception.hw_args, raise_intf.args):
                connect_to_MonitorIntf(a_src, a_dst)

        if raising_flag is not None:
            raising_flag(raise_intf.vld)

        return [
            raise_intf.vld(1),
        ]

    def hw_catch(self, exception_cls: Optional[Union[Type[InHwError], Tuple[Type[InHwError], ...]]]=None) -> List[Tuple[InHwError, ExceptionHandleInterface]]:
        """
        Catch all uncatched exceptions by exception class.

        :param exception_cls: An class on exceptions which should be catched (An exception is catched if its class is a subclass of exception_cls).
        :note: Catching exception means getting IO for exception handling in this context.
            You need to drive all interfaces and possibly re-raise for those which should not be catched.
        :returns: List of tuples (exception, interface) for every uncatched exception in current scope (includes children).
            (Due to parallel nature of hardware it is a list and exceptions may be raised simulately.)
        """
        for i in self.parent._private_interfaces:
            if isinstance(i, ExceptionHandleInterface) and\
                    isinstance(i._exception, exception_cls) and \
                    not i.rd._sig.drivers:
                yield i

        for i in tuple(self.parent._interfaces):
            # if interface is public it automaically means that exception is not handled
            # in this Unit yet
            if isinstance(i, ExceptionHandleInterface) and\
                    i._direction == INTF_DIRECTION.SLAVE and \
                    isinstance(i._exception, exception_cls):
                self._Unit_makePublicIntfPrivateInImpl(i)
                yield i

        for u in self.parent._units:
            for i in u._interfaces:
                if isinstance(i, ExceptionHandleInterface) and \
                        not i.rd._sig.drivers and\
                        isinstance(i._exception, exception_cls):
                    yield i

    def propagate(self):
        """
        Propagate uncatched exceptions from this :class:`hwt.synthesizer.unit.Unit` instance and its children
        to IO of this :class:`hwt.synthesizer.unit.Unit` instance.

        :note: The exception is considered uncached if its rd signal is not driven.
        """
        for i in tuple(self.parent._private_interfaces):
            if isinstance(i, ExceptionHandleInterface) and not i.rd._sig.drivers:
                raise NotImplementedError(i)

        for u in self.parent._units:
            for i in u._interfaces:
                if isinstance(i, ExceptionHandleInterface) and not i.rd._sig.drivers:
                    raise_intf = i.__copy__()._m()
                    self._Unit_registerPublicIntfInImpl(
                        raise_intf,
                        AbstractComponentBuilder._findSuitableName(self, i._exception.__class__.__name__)
                    )
                    object.__setattr__(self.parent, raise_intf._name, raise_intf)
                    raise_intf(i)

