from hwt.hdl.constants import WRITE, READ
from hwtLib.sim.abstractMemSpaceMaster import AbstractMemSpaceMaster


class BramPortSimMemSpaceMaster(AbstractMemSpaceMaster):
    """
    Controller of BramPort simulation agent which keeps track of transactions
    and allows struct like data access
    """
    def _writeAddr(self, addrChannel, addr, size):
        addrChannel.data.append(addr)

    def _write(self, addr, size, data, mask, onDone=None):
        if onDone:
            raise NotImplementedError()

        w = self._bus._ag.requests
        # (request type, address, [write data])
        w.append((WRITE, addr, data))

    def _read(self, addr, size, onDone):
        if onDone:
            raise NotImplementedError()

        r = self._bus._ag.requests
        # (request type, address, [write data])
        r.append((READ, addr))
