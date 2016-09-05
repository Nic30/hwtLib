from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.intfLvl import connect, Unit
from hdl_toolkit.synthesizer.shortcuts import toRtl


class SimpleComentedUnit(Unit):
    """
    This is comment for SimpleComentedUnit entity, it will be rendered up to entity.
    Implementation allows you to use what ever you wont.
    Do not forget that inherited classes have it's own docstring even if it was not specified (None). 
    """
    
    def _declr(self):
        with self._asExtern():
            self.a = Signal()
            self.b = Signal()
    
    def _impl(self):
        self.b ** self.a


class SimpleComentedUnit2(SimpleComentedUnit):
    """single line"""
    pass

class SimpleComentedUnit3(SimpleComentedUnit2):
    pass

SimpleComentedUnit3.__doc__ = "dynamically generated, for example loaded from file or builded from unit content"


if __name__ == "__main__":
    print(toRtl(SimpleComentedUnit))
    print(toRtl(SimpleComentedUnit2))
    print(toRtl(SimpleComentedUnit3))