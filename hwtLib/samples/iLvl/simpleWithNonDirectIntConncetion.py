from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.intfLvl import Unit


class SimpleWithNonDirectIntConncetion(Unit):
    """
    Example of fact that interfaces does not have to be only extern
    the can be used even for connection inside unit
    """
    
    def _declr(self):
        with self._asExtern():
            self.a = Signal()
            self.c = Signal()
        self.b = Signal()
        
    def _impl(self):
        self.b ** self.a
        self.c ** self.b

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    print(toRtl(SimpleWithNonDirectIntConncetion()))
