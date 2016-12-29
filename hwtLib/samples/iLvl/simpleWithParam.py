#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import Signal
from hwt.intfLvl import Param, Unit


class SimpleUnitWithParam(Unit):
    """
    Simple parametrized unit.
    """
    def _config(self):
        # declaration of parameter DATA_WIDTH with default value 8
        # type of parameter is determined from used value 
        self.DATA_WIDTH = Param(8)
        
    def _declr(self):
        # vecT is shortcut for vector type first parameter is width, second optional is signed flag
        dt = vecT(self.DATA_WIDTH)
        # dt is now type vector with width specified by parameter DATA_WIDTH
        # it means it is 8bit width we specify datatype for every signal
        self.a = Signal(dtype=dt)
        self.b = Signal(dtype=dt)
        
    def _impl(self):
        self.b ** self.a
        
        
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = SimpleUnitWithParam()
    
    # we can now optionally set our parameter to any chosen value
    u.DATA_WIDTH.set(1024)
    
    print(toRtl(u))

# expected result
#--
#--    Simple parametrized unit.
#--
#library IEEE;
#use IEEE.std_logic_1164.all;
#use IEEE.numeric_std.all;
#
#ENTITY SimpleUnitWithParam IS
#    GENERIC (
#        DATA_WIDTH : INTEGER := 1024
#    );
#    PORT (a : IN STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0);
#        b : OUT STD_LOGIC_VECTOR(DATA_WIDTH - 1 DOWNTO 0)
#    );
#END SimpleUnitWithParam;
#
#ARCHITECTURE rtl OF SimpleUnitWithParam IS
#    
#    
#    
#BEGIN
#    
#    b <= a;
#    
#END ARCHITECTURE rtl;
