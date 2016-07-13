from hdl_toolkit.intfLvl import connect, Unit
from hdl_toolkit.interfaces.std import Ap_none


class SimpleUnit(Unit):
    """
    In order to create a new unit you have to make new class derived from Unit.
    """
    def _declr(self):
        """
        _declr() is like header of Unit.
        There you have to declare things which should be visible from outside.    
        """ 
        with self._asExtern():
            # we use _asExtern() to mark interfaces "a" and "b" as external, this means they will be
            # interfaces of Entity and all other units can connect anything to these interfaces   
            self.a = Sig()
            self.b = Sig()

    def _impl(self):
        """
        _impl() is like body of unit. 
        Logic and connections are specified in this unit.
        """
        # connect() creates assignment. First parameter is source rest are destinations.

        connect(self.a, self.b) # a drives b
        # directions of a and b interfaces are derived automatically, if signal has driver it is output

if __name__ == "__main__": # alias python main function
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    print(toRtl(SimpleUnit))
