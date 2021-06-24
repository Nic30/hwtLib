from hwt.hdl.constants import WRITE, READ
from hwt.interfaces.agents.handshaked import HandshakedReadListener
from hwt.interfaces.agents.tuleWithCallback import TupleWithCallback
from hwtLib.sim.abstractMemSpaceMaster import AbstractMemSpaceMaster


class AvalonMmMemSpaceMaster(AbstractMemSpaceMaster):
    """
    Controller of AvalonMM simulation agent which keeps track of axi lite transactions
    and aggregates them to proper register names on target bus
    """

    def __init__(self, bus, registerMap):
        super(AvalonMmMemSpaceMaster, self).__init__(bus, registerMap)
        self._read_listener = None

    def _write(self, addr, size, data, mask, onDone=None):
        """
        add write address and write data to agent

        :param onDone: callback function(sim) -> None
        """
        bus = self._bus._ag
        burstSize = 1
        bus.req.append(TupleWithCallback(WRITE, addr, burstSize, data, mask, onDone=onDone))

    def _read(self, addr, size, onDone=None):
        """
        add read address transaction to agent
        """
        bus = self._bus._ag
        burstsize = 1
        bus.req.append((READ, addr, burstsize, None, None))

        if onDone:
            raise NotImplementedError()
            if self._read_listener is None:
                self._read_listener = HandshakedReadListener(self._bus.r._ag)

            self._read_listener.register(self._r_planed_words_cnt, onDone)
