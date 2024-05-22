from typing import Optional, Set

from hwt.hwIO import HwIO
from hwt.hwModule import HwModule
from ipCorePackager.constants import INTF_DIRECTION


def connect_to_const(val, hwIO: HwIO, exclude=None):
    for _ in _connect_to_const_it(val, hwIO, exclude):
        pass


def _connect_to_const_it(val, hwIO: HwIO, exclude: Optional[Set[HwIO]]):
    """
    Connect constant to all output ports, used mainly during the debbug
    to disable interface
    """
    if exclude is not None and hwIO in exclude:
        return

    if hwIO._hwIOs:
        for cHwIO in hwIO._hwIOs:
            yield from _connect_to_const_it(val, cHwIO, exclude)
    else:
        if hwIO._direction == INTF_DIRECTION.SLAVE:
            yield hwIO(val)


class EmptyHwModule(HwModule):
    """
    :class:`hwt.hwModule.HwModule` used for prototyping all output interfaces are connected
    to _def_val and this is only think which architecture contains

    :cvar _def_val: this value is used to initialize all signals
    """
    _def_val = None

    def hwImpl(self):
        for cHwIO in self._hwIOs:
            connect_to_const(self._def_val, cHwIO)
