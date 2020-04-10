from hwt.hdl.constants import WRITE, READ
from hwtLib.sim.abstractMemSpaceMaster import AbstractMemSpaceMaster


class Mi32SimMemSpaceMaster(AbstractMemSpaceMaster):
    """
    Controller of BramPort simulation agent which keeps track of transactions
    and allows struct like data access

    :ivar ~.req: request data, items are tuples (READ, address)
        or (WRITE, address, data, be_mask)
    """

    def _write(self, addr, size, data, mask, onDone=None):
        if onDone:
            raise NotImplementedError()

        w = self._bus._ag.requests
        # (request type, address, [write data], byte_en)
        w.append((WRITE, addr, data, mask))

    def _read(self, addr, size, onDone):
        if onDone:
            raise NotImplementedError()

        r = self._bus._ag.requests
        # (request type, address, [write data])
        r.append((READ, addr))
