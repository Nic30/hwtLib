from typing import Union, Type

from hwt.hdl.types.structValBase import StructValBase
from hwt.interfaces.std import VldSynced, Signal
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.rtlLevel.mainBases import RtlSignalBase
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwtLib.clocking.vldSynced_cdc import VldSyncedCdc


class MonitorIntf(Interface):
    """
    Interfaces same as template interface, but with all signals as an input
    """

    def __init__(self, template_interface):
        self._template_interface = template_interface
        super(MonitorIntf, self).__init__()

    @staticmethod
    def _bound_intf(template_interface, cls=None):
        if cls is None:
            cls = MonitorIntf

        class BoundedMonitorIntf(cls):

            def __init__(self):
                super(BoundedMonitorIntf, self).__init__(template_interface)

        return BoundedMonitorIntf

    def _config(self):
        """
        Copy config from template interface
        """
        tmpl = self._template_interface
        for p in tmpl._params:
            setattr(self, p._name, p.get_value())

    def _declr(self):
        """
        Create interfaces same as on template interface,
        but make them always input
        """
        tmpl = self._template_interface
        for i in tmpl._interfaces:
            setattr(self, i._name, monitor_of(i))


class MonitorIntfVldSynced(VldSynced):

    def __init__(self, template_interface):
        self._template_interface = template_interface
        super(MonitorIntfVldSynced, self).__init__()

    def _config(self):
        MonitorIntf._config(self)

    def _declr(self):
        self.data = MonitorIntf(self._template_interface)
        self.vld = Signal()


class MonitorIntfVldSyncedCdc(VldSyncedCdc):

    def __init__(self, template_interface):
        """
        :param template_interface: an Interface instance which will be monitored,
            used as template for this interface
        """
        intf_cls = MonitorIntf._bound_intf(
            template_interface, cls=MonitorIntfVldSynced)
        self._template_interface = template_interface
        super(MonitorIntfVldSyncedCdc, self).__init__(intf_cls)


def monitor_of(intf: Union[Interface, RtlSignal]):
    """
    Create a monitor interface for specified interface
    (monitor interface is an interface which reads all signals of choosen interface)
    """
    if isinstance(intf, Interface) and intf._interfaces:
        return MonitorIntf(intf)
    else:
        if not isinstance(intf, (Signal, RtlSignalBase)):
            raise NotImplementedError(intf)
        return Signal(dtype=intf._dtype)


def _connect_MonitorIntf(src: MonitorIntf, dst):
    if src._interfaces:
        for _src in src._interfaces:
            _dst = getattr(dst, _src._name)
            yield from _connect_MonitorIntf(_src, _dst)
    else:
        src = src._reinterpret_cast(dst._dtype)
        yield dst(src)


def connect_MonitorIntf(src: MonitorIntf, dst):
    """
    Connect signal by signal and ignore the directions of struct interface
    (check only direction of low level signals)
    """
    return list(_connect_MonitorIntf(src, dst))


def _connect_to_MonitorIntf(src, dst: MonitorIntf):
    if isinstance(dst, (StructValBase, RtlSignal)):
        if src._interfaces:
            for _src in src._interfaces:
                _dst = getattr(dst, _src._name)
                yield from _connect_to_MonitorIntf(_src, _dst)
            return
    else:
        if dst._interfaces:
            for _dst in dst._interfaces:
                _src = getattr(src, _dst._name)
                yield from _connect_to_MonitorIntf(_src, _dst)
            return
    yield dst(src)


def connect_to_MonitorIntf(src, dst: MonitorIntf):
    """
    Connect signal by signal and ignore the directions of struct interface
    (check only direction of low level signals)
    """
    return list(_connect_to_MonitorIntf(src, dst))


class MonitorIntfReg(Unit):

    def __init__(self, intfCls: Type[MonitorIntf]):
        self.intfCls = intfCls
        Unit.__init__(self)

    def _config(self):
        Unit._config(self)
