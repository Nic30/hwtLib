#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import Signal
from hwt.intfLvl import Unit


class SimpleUnit(Unit):
    """
    In order to create a new unit you have to make new class derived from Unit.
    """
    def _declr(self):
        """
        _declr() is like header of Unit.
        There you have to declare things which should be visible from outside.    
        """ 
        # interfaces "a" and "b" are accessible from outside when declared in _declr method, 
        # this means they will be interfaces of Entity and all other units can connect anything to these interfaces   
        self.a = Signal()
        self.b = Signal()

    def _impl(self):
        """
        _impl() is like body of unit. 
        Logic and connections are specified in this unit.
        """
        # ** operator creates assignment. First parameter is source rest are destinations.

        self.b ** self.a  # a drives b
        # directions of a and b interfaces are derived automatically, if signal has driver it is output

if __name__ == "__main__":  # alias python main function
    # toRtl can be imported anywhere but we prefer to import it only when this script is running as main
    from hwt.synthesizer.shortcuts import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    print(toRtl(SimpleUnit))
