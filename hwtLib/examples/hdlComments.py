#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.std import Signal
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.utils import toRtl


class SimpleComentedUnit(Unit):
    """
    This is comment for SimpleComentedUnit entity, it will be rendered before entity as comment.
    Do not forget that class inheritance does apply for docstring as well.
    """

    def _declr(self):
        self.a = Signal()
        self.b = Signal()._m()

    def _impl(self):
        self.b(self.a)


simpleComentedUnitExpected =\
"""
--
--    This is comment for SimpleComentedUnit entity, it will be rendered before entity as comment.
--    Do not forget that class inheritance does apply for docstring as well.
--
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY SimpleComentedUnit IS
    PORT (a: IN STD_LOGIC;
        b: OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleComentedUnit IS

BEGIN

    b <= a;

END ARCHITECTURE;
"""


class SimpleComentedUnit2(SimpleComentedUnit):
    """single line"""
    pass

simpleComentedUnit2Expected =\
"""
--single line
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY SimpleComentedUnit2 IS
    PORT (a: IN STD_LOGIC;
        b: OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleComentedUnit2 IS

BEGIN

    b <= a;

END ARCHITECTURE;
"""


class SimpleComentedUnit3(SimpleComentedUnit2):
    pass


SimpleComentedUnit3.__doc__ = "dynamically generated, for example loaded from file or builded from unit content"

simpleComentedUnit3Expected = \
"""
--dynamically generated, for example loaded from file or builded from unit content
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY SimpleComentedUnit3 IS
    PORT (a: IN STD_LOGIC;
        b: OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF SimpleComentedUnit3 IS

BEGIN

    b <= a;

END ARCHITECTURE;
"""


if __name__ == "__main__":
    print(toRtl(SimpleComentedUnit))
    print(toRtl(SimpleComentedUnit2))
    print(toRtl(SimpleComentedUnit3))
