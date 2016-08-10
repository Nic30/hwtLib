from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.intfLvl import connect, Param, Unit


class SimpleUnitWithParam(Unit):
    """
    Simple parametrized unit.
    """
    def _config(self):
        # declaration of parameter DATA_WIDTH with default value 8
        self.DATA_WIDTH = Param(8)
        
    def _declr(self):
        # vecT is shortcut for vector type first parameter is width, second optional is signed flag
        dt = vecT(self.DATA_WIDTH)
        # dt is now vector with width specified by parameter DATA_WIDTH
        # it means it is 8bit width 
        with self._asExtern():
            # we specify datatype for every signal
            self.a = Signal(dtype=dt)
            self.b = Signal(dtype=dt)
        
    def _impl(self):
        connect(self.a, self.b)
        
        
if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    print(toRtl(SimpleUnitWithParam))
