from hwt.hdlObjects.constants import WRITE, READ
from hwtLib.sim.abstractMemSpaceMaster import AbstractMemSpaceMaster


class IPFISimMaster(AbstractMemSpaceMaster):
    """
    Simulation address space master for IPIF interface
    """
    def _write(self, addr, size, data, mask):
        w = self._bus._ag.requests
        # (request type, address, [write data])
        w.append((WRITE, addr, data, mask))

    def _read(self, addr, size):
        r = self._bus._ag.requests
        # (request type, address, [write data])
        r.append((READ, addr))
