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
        # note that interfaces has to be properties of this object
        # whis is kind of registration and without it, it can not be discovered
        self.a = Signal()
        self.b = Signal()

    def _impl(self):
        """
        _impl() is like body of unit. 
        Logic and connections are specified in this function.
        """

        # ** operator creates assignment. First parameter is source rest are destinations.
        self.b ** self.a  # a drives b
        # directions of a and b interfaces are derived automatically, if signal has driver it is output

if __name__ == "__main__":  # alias python main function
    # toRtl can be imported anywhere but we prefer to import it only when this script is running as main
    from hwt.synthesizer.shortcuts import toRtl
    # we create instance of our unit
    u = SimpleUnit()
    # there is more of synthesis methods. toRtl() returns formated hdl string
    print(toRtl(u))

# expected Output (without # ofcourse)
#--
#--    In order to create a new unit you have to make new class derived from Unit.
#--
#library IEEE;
#use IEEE.std_logic_1164.all;
#use IEEE.numeric_std.all;
#
#ENTITY SimpleUnit IS
#    PORT (a : IN STD_LOGIC;
#        b : OUT STD_LOGIC
#    );
#END SimpleUnit;
#
#ARCHITECTURE rtl OF SimpleUnit IS
#    
#    
#    
#BEGIN
#    
#    b <= a;
#    
#END ARCHITECTURE rtl;