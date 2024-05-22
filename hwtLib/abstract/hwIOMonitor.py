from typing import Union, Type

from hwt.hdl.types.structValBase import HStructConstBase
from hwt.hwIO import HwIO
from hwt.hwIOs.std import HwIODataVld, HwIOSignal
from hwt.hwModule import HwModule
from hwt.mainBases import RtlSignalBase
from hwt.pyUtils.typingFuture import override
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwtLib.clocking.vldSynced_cdc import VldSyncedCdc


class HwIOMonitor(HwIO):
    """
    Interfaces same as template interface, but with all signals as an input
    """

    def __init__(self, templateHwIO: HwIO):
        self._templateHwIO = templateHwIO
        super(HwIOMonitor, self).__init__()

    @staticmethod
    def _boundHwIO(templateHwIO, cls=None):
        if cls is None:
            cls = HwIOMonitor

        class HwIOBoundedMonitor(cls):

            def __init__(self):
                super(HwIOBoundedMonitor, self).__init__(templateHwIO)

        return HwIOBoundedMonitor

    @override
    def hwConfig(self):
        """
        Copy config from template interface
        """
        tmpl = self._templateHwIO
        for p in tmpl._hwParams:
            setattr(self, p._name, p.get_value())

    @override
    def hwDeclr(self):
        """
        Create interfaces same as on template interface,
        but make them always input
        """
        tmpl = self._templateHwIO
        for cHwIO in tmpl._hwIOs:
            setattr(self, cHwIO._name, monitor_of(cHwIO))


class HwIOMonitorDataVld(HwIODataVld):

    def __init__(self, templateHwIO):
        self._templateHwIO = templateHwIO
        super(HwIOMonitorDataVld, self).__init__()

    @override
    def hwConfig(self):
        HwIOMonitor.hwConfig(self)

    @override
    def hwDeclr(self):
        self.data = HwIOMonitor(self._templateHwIO)
        self.vld = HwIOSignal()


class HwIOMonitorDataVldCdc(VldSyncedCdc):

    def __init__(self, templateHwIO):
        """
        :param templateHwIO: an HwIO instance which will be monitored,
            used as template for this interface
        """
        hwIOcls = HwIOMonitor._boundHwIO(
            templateHwIO, cls=HwIOMonitorDataVld)
        self._templateHwIO = templateHwIO
        super(HwIOMonitorDataVldCdc, self).__init__(hwIOcls)


def monitor_of(hwIO: Union[HwIO, RtlSignal]):
    """
    Create a monitor interface for specified interface
    (monitor interface is an interface which reads all signals of choosen interface)
    """
    if isinstance(hwIO, HwIO) and hwIO._hwIOs:
        return HwIOMonitor(hwIO)
    else:
        if not isinstance(hwIO, (HwIOSignal, RtlSignalBase)):
            raise NotImplementedError(hwIO)
        return HwIOSignal(dtype=hwIO._dtype)


def _connect_HwIOMonitor(src: HwIOMonitor, dst):
    if src._hwIOs:
        for _src in src._hwIOs:
            _dst = getattr(dst, _src._name)
            yield from _connect_HwIOMonitor(_src, _dst)
    else:
        src = src._reinterpret_cast(dst._dtype)
        yield dst(src)


def connect_HwIOMonitor(src: HwIOMonitor, dst):
    """
    Connect signal by signal and ignore the directions of struct interface
    (check only direction of low level signals)
    """
    return list(_connect_HwIOMonitor(src, dst))


def _connect_to_HwIOMonitor(src, dst: HwIOMonitor):
    if isinstance(dst, (HStructConstBase, RtlSignal)):
        if src._hwIOs:
            for _src in src._hwIOs:
                _dst = getattr(dst, _src._name)
                yield from _connect_to_HwIOMonitor(_src, _dst)
            return
    else:
        if dst._hwIOs:
            for _dst in dst._hwIOs:
                _src = getattr(src, _dst._name)
                yield from _connect_to_HwIOMonitor(_src, _dst)
            return
    yield dst(src)


def connect_to_HwIOMonitor(src, dst: HwIOMonitor):
    """
    Connect signal by signal and ignore the directions of struct interface
    (check only direction of low level signals)
    """
    return list(_connect_to_HwIOMonitor(src, dst))


class HwIOMonitorReg(HwModule):

    def __init__(self, hwIOCls: Type[HwIOMonitor]):
        self.hwIOCls = hwIOCls
        HwModule.__init__(self)

    @override
    def hwConfig(self):
        HwModule.hwConfig(self)
