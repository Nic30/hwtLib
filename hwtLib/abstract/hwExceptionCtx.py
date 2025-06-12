from collections import deque
from typing import Type, List, Tuple, Optional, Union

from hwt.code import If
from hwt.hwIOs.std import HwIORdVldSync
from hwt.hwModule import HwModule
from hwt.hObjList import HObjList
from hwt.mainBases import RtlSignalBase
from hwt.synthesizer.interfaceLevel.utils import HwIO_walkSignals
from hwtLib.abstract.componentBuilder import AbstractComponentBuilder
from hwtLib.abstract.debug_bus_monitor import monitor_of, connect_to_HwIOMonitor
from ipCorePackager.constants import DIRECTION, INTF_DIRECTION
from hwt.pyUtils.typingFuture import override


class InHwError(Exception):
    """
    A base class for exceptions which are translated to hardware
    and handle in runtime of the hardware.

    :ivar Deque[HwModule] hw_traceback: traceback
    """

    def __init__(self, hw_args=None, *args, **kwargs):
        super(InHwError, self).__init__(*args, **kwargs)
        self.hw_traceback = deque()
        if hw_args is None:
            hw_args = ()
        else:
            assert isinstance(hw_args, (tuple, list))
        self.hw_args = hw_args


class ExceptionHandleInterface(HwIORdVldSync):

    def __init__(self, exception:InHwError, masterDir=DIRECTION.OUT,
                 loadConfig=True):
        HwIORdVldSync.__init__(self, masterDir=masterDir, loadConfig=loadConfig)
        self._exception = exception

    @override
    def hwDeclr(self):
        HwIORdVldSync.hwDeclr(self)
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
        :class:`hwt.hwModule.HwModule` instance.
    """

    def __init__(self, parent: HwModule, name="raise"):
        self.parent = parent
        self.compId = 0
        self.catch_instances = []
        self.name = name

    def _HwModule_registerPublicHwIOInImpl(self, hwIO: ExceptionHandleInterface, name:str, onParentPropertyPath: tuple[Union[str, int], ...]):
        p = self.parent
        p._registerHwIO(name, hwIO, onParentPropertyPath, False)
        p._loadHwIODeclarations(hwIO, True)
        hwIO._signalsForHwIO(
            p._rtlCtx, p._rtlCtx.hwIOs, p._store_manager.name_scope,
            reverse_dir=True)

    def _HwModule_makePublicHwIOPrivateInImpl(self, hwIO: ExceptionHandleInterface):
        parent_m = hwIO._parent
        while not isinstance(parent_m, HwModule):
            parent_m = parent_m._parent

        parent_m._hwIOs.remove(hwIO)
        parent_m._private_hwIOs.append(hwIO)

        for s in HwIO_walkSignals(hwIO):
            if s._direction == INTF_DIRECTION.SLAVE:
                ep = s._sig._rtlEndpoints
                ep.remove(s._hdlPort)

            elif s._direction == INTF_DIRECTION.MASTER:
                dr = s._sig._rtlDrivers
                dr.remove(s._hdlPort)
            else:
                raise ValueError(s._direction)

            s._sig._rtlCtx.hwIOs.pop(s._sig)
            self.parent._rtlCtx.hwModDec.ports.remove(s._hdlPort)
            s._hdlPort = None
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
        :return: An expression which triggers the exception handling.
        """
        assert isinstance(exception, InHwError)
        err_name = exception.__class__.__name__
        p = self.parent

        # add a raise interace in impl phase of the HwModule instance
        raiseHwIO = ExceptionHandleInterface(exception)._m()
        onParentPropertyPath: tuple[Union[str, int], ...] = (AbstractComponentBuilder._findSuitableName(self, err_name), )
        self._HwModule_registerPublicHwIOInImpl(
            raiseHwIO,
            onParentPropertyPath[0],
            onParentPropertyPath
        )
        object.__setattr__(p, raiseHwIO._name, raiseHwIO)

        # create a flag which means that the error is waiting
        err_pending = p._reg(f"{self.name:s}_{err_name:s}_pending", def_val=0)
        if pending_flag is not None:
            pending_flag(err_pending)

        If(err_pending,
           err_pending(~raiseHwIO.rd),
        ).Else(
           err_pending(raiseHwIO.vld & ~raiseHwIO.rd),
        )
        raiseHwIO.vld._sig._nop_val = raiseHwIO.vld._sig._dtype.from_py(0)
        if exception.hw_args:
            for a_src, a_dst in zip(exception.hw_args, raiseHwIO.args):
                connect_to_HwIOMonitor(a_src, a_dst)

        if raising_flag is not None:
            raising_flag(raiseHwIO.vld)

        return [
            raiseHwIO.vld(1),
        ]

    def hw_catch(self, exception_cls: Optional[Union[Type[InHwError], Tuple[Type[InHwError], ...]]]=None)\
            -> List[Tuple[InHwError, ExceptionHandleInterface]]:
        """
        Catch all uncatched exceptions by exception class.

        :param exception_cls: An class on exceptions which should be catched (An exception is catched if its class is a subclass of exception_cls).
        :note: Catching exception means getting IO for exception handling in this context.
            You need to drive all interfaces and possibly re-raise for those which should not be catched.
        :return: List of tuples (exception, interface) for every uncatched exception in current scope (includes children).
            (Due to parallel nature of hardware it is a list and exceptions may be raised simulately.)
        """
        for hwIO in self.parent._private_hwIOs:
            if isinstance(hwIO, ExceptionHandleInterface) and\
                    isinstance(hwIO._exception, exception_cls) and \
                    not hwIO.rd._sig._rtlDrivers:
                yield hwIO

        for hwIO in tuple(self.parent._hwIOs):
            # if interface is public it automatically means that exception is not handled
            # in this HwModule yet
            if isinstance(hwIO, ExceptionHandleInterface) and\
                    hwIO._direction == INTF_DIRECTION.SLAVE and \
                    isinstance(hwIO._exception, exception_cls):
                self._HwModule_makePublicHwIOPrivateInImpl(hwIO)
                yield hwIO

        for u in self.parent._subHwModules:
            for hwIO in u._hwIOs:
                if isinstance(hwIO, ExceptionHandleInterface) and \
                        not hwIO.rd._sig._rtlDrivers and\
                        isinstance(hwIO._exception, exception_cls):
                    yield hwIO

    def propagate(self):
        """
        Propagate uncatched exceptions from this :class:`hwt.hwModule.HwModule` instance and its children
        to IO of this :class:`hwt.hwModule.HwModule` instance.

        :note: The exception is considered uncached if its rd signal is not driven.
        """
        for hwIO in tuple(self.parent._private_hwIOs):
            if isinstance(hwIO, ExceptionHandleInterface) and not hwIO.rd._sig._rtlDrivers:
                raise NotImplementedError(hwIO)

        for u in self.parent._subHwModules:
            for hwIO in u._hwIOs:
                if isinstance(hwIO, ExceptionHandleInterface) and not hwIO.rd._sig._rtlDrivers:
                    raise_hwIO = hwIO.__copy__()._m()
                    name = AbstractComponentBuilder._findSuitableName(self, hwIO._exception.__class__.__name__)
                    self._HwModule_registerPublicHwIOInImpl(
                        raise_hwIO,
                        name,
                        (name, )
                    )
                    object.__setattr__(self.parent, raise_hwIO._name, raise_hwIO)
                    raise_hwIO(hwIO)

