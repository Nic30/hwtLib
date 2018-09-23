from hwt.interfaces.agents.handshaked import HandshakedReadListener

from hwtLib.amba.axi3Lite import Axi3Lite
from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.sim.abstractMemSpaceMaster import AbstractMemSpaceMaster


class TupleWithCallback(tuple):
    def __new__(cls, *args):
        return tuple.__new__(cls, args)


class AxiLiteMemSpaceMaster(AbstractMemSpaceMaster):
    """
    Controller of AxiLite simulation agent which keeps track of transactions
    and allows struct like data access
    """

    def __init__(self, bus, registerMap):
        super(AxiLiteMemSpaceMaster, self).__init__(bus, registerMap)
        self._r_planed_words_cnt = 0
        self._w_planed_words_cnt = 0
        self._read_listener = None
        if isinstance(bus, Axi4Lite):
            self._writeAddr = self._axi4lite_writeAddr
        elif isinstance(bus, Axi3Lite):
            self._writeAddr = self._axi3lite_writeAddr
        else:
            raise TypeError(bus)

    def _axi4lite_writeAddr(self, addrChannel, addr, size):
        """
        add address transaction to addr channel of agent
        """
        prot = 0 
        addrChannel.data.append((addr, prot))

    def _axi3lite_writeAddr(self, addrChannel, addr, size):
        """
        add address transaction to addr channel of agent
        """
        addrChannel.data.append(addr)

    def _writeData(self, data, mask, onDone=None):
        """
        add data write transaction to agent

        :param onDone: callback function(sim) -> None
        """
        if onDone:
            d = TupleWithCallback(data, mask)
            d.onDone = onDone
        else:
            d = (data, mask)

        self._bus._ag.w.data.append(d)

    def _write(self, addr, size, data, mask, onDone=None):
        """
        add write address and write data to agent

        :param onDone: callback function(sim) -> None
        """
        self._writeAddr(self._bus._ag.aw, addr, size)
        self._w_planed_words_cnt += 1
        self._writeData(data, mask, onDone=onDone)

    def _read(self, addr, size, onDone=None):
        """
        add read address transaction to agent
        """
        self._writeAddr(self._bus._ag.ar, addr, size)
        self._r_planed_words_cnt += 1

        if onDone:
            if self._read_listener is None:
                self._read_listener = HandshakedReadListener(self._bus.r._ag)

            self._read_listener.register(self._r_planed_words_cnt, onDone)
