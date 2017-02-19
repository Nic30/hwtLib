from hwtLib.sim.abstractMemSpaceMaster import AbstractMemSpaceMaster


class AxiLiteMemSpaceMaster(AbstractMemSpaceMaster):
    def _writeAddr(self, addrChannel, addr, size):
        raise NotImplementedError()
    
    def _writeData(self, data, mask):
        raise NotImplementedError()
    
    def _write(self, addr, size, data, mask, thenFn=None):
        self._writeAddr(self.bus.aw, addr, size)
        self._writeData(data, mask)     

class Axi3MemSpaceMaster(AxiLiteMemSpaceMaster):
    def _writeAddr(self, addrChannel, addr, size):
        raise NotImplementedError()
    
    def _writeData(self, data, mask):
        raise NotImplementedError()
    
    