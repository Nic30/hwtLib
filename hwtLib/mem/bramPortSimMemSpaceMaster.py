from hwt.hdlObjects.constants import WRITE, READ
from hwtLib.sim.abstractMemSpaceMaster import AbstractMemSpaceMaster


class BramPortSimMemSpaceMaster(AbstractMemSpaceMaster):
    def _writeAddr(self, addrChannel, addr, size):
        addrChannel.data.append(addr)

    def _write(self, addr, size, data, mask, thenFn=None):
        w = self._bus._ag.requests
        # (request type, address, [write data])
        w.append((WRITE, addr, data))
        if thenFn:
            raise NotImplementedError()

    def _read(self, addr, size, thenFn):
        r = self._bus._ag.requests
        # (request type, address, [write data])
        r.append((READ, addr))
        if thenFn:
            raise NotImplementedError()