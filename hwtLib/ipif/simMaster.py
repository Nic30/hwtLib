from hwt.hdl.constants import WRITE, READ
from hwtLib.sim.abstractMemSpaceMaster import AbstractMemSpaceMaster


class IPFISimMaster(AbstractMemSpaceMaster):
    """
    Simulation address space master for IPIF interface
    """
    def _write(self, addr, size, data, mask, onDone=None):
        if onDone:
            raise NotImplementedError()

        w = self._bus._ag.requests
        # (request type, address, [write data])
        w.append((WRITE, addr, data, mask))
        
    def _read(self, addr, size, onDone=None):
        if onDone:
            raise NotImplementedError()

        r = self._bus._ag.requests
        # (request type, address, [write data])
        r.append((READ, addr))
