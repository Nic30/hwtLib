from hwt.hdl.constants import WRITE, READ
from hwtLib.sim.abstractMemSpaceMaster import AbstractMemSpaceMaster


class BramPortSimMemSpaceMaster(AbstractMemSpaceMaster):
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
