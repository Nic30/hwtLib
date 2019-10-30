import unittest

from hwt.code import Concat
from hwt.interfaces.std import Signal, VectSignal
from hwt.serializer.mode import serializeExclude, serializeOnce, \
    serializeParamsUniq
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.param import Param
from hwt.synthesizer.utils import toRtl


class SimpeUnit(Unit):
    def _declr(self):
        self.a = Signal()._m()

    def _impl(self):
        self.a(1)


@serializeExclude
class ExcludedUnit(SimpeUnit):
    pass


@serializeOnce
class OnceUnit(SimpeUnit):
    pass


@serializeParamsUniq
class ParamsUniqUnit(SimpeUnit):
    def _config(self):
        self.A = Param(0)
        self.B = Param(1)


class ExampleA(Unit):
    def _declr(self):
        self.a = VectSignal(7)._m()
        self.u0 = ExcludedUnit()
        self.u1 = ExcludedUnit()
        self.u2 = OnceUnit()
        self.u3 = OnceUnit()
        self.u4 = OnceUnit()
        self.u5 = ParamsUniqUnit()
        self.u6 = ParamsUniqUnit()
        self.u7 = ParamsUniqUnit()
        self.u7.B = 12

    def _impl(self):
        self.a(Concat(*[getattr(self, "u%d" % i).a for i in range(7)]))


expected_vhdl = """--Object of class Entity, "ExcludedUnit" was not serialized as specified
--Object of class Architecture, "rtl" was not serialized as specified
--Object of class Entity, "ExcludedUnit" was not serialized as specified
--Object of class Architecture, "rtl" was not serialized as specified
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY OnceUnit IS
    PORT (a: OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF OnceUnit IS
BEGIN
    a <= '1';
END ARCHITECTURE;
--Object of class Entity, "OnceUnit" was not serialized as specified
--Object of class Architecture, "rtl" was not serialized as specified
--Object of class Entity, "OnceUnit" was not serialized as specified
--Object of class Architecture, "rtl" was not serialized as specified
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY u5 IS
    GENERIC (A: string := "0";
        B: string := "1"
    );
    PORT (a_0: OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF u5 IS
BEGIN
    a_0 <= '1';
END ARCHITECTURE;
--Object of class Entity, "u5" was not serialized as specified
--Object of class Architecture, "rtl" was not serialized as specified
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY u7 IS
    GENERIC (A: string := "0";
        B: string := "12"
    );
    PORT (a_0: OUT STD_LOGIC
    );
END ENTITY;

ARCHITECTURE rtl OF u7 IS
BEGIN
    a_0 <= '1';
END ARCHITECTURE;
library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;

ENTITY ExampleA IS
    PORT (a: OUT STD_LOGIC_VECTOR(6 DOWNTO 0)
    );
END ENTITY;

ARCHITECTURE rtl OF ExampleA IS
    SIGNAL sig_u0_a: STD_LOGIC;
    SIGNAL sig_u1_a: STD_LOGIC;
    SIGNAL sig_u2_a: STD_LOGIC;
    SIGNAL sig_u3_a: STD_LOGIC;
    SIGNAL sig_u4_a: STD_LOGIC;
    SIGNAL sig_u5_a_0: STD_LOGIC;
    SIGNAL sig_u6_a_0: STD_LOGIC;
    SIGNAL sig_u7_a_0: STD_LOGIC;
    COMPONENT ExcludedUnit IS
       PORT (a: OUT STD_LOGIC
       );
    END COMPONENT;

    COMPONENT OnceUnit IS
       PORT (a: OUT STD_LOGIC
       );
    END COMPONENT;

    COMPONENT u5 IS
       GENERIC (A: string := "0";
            B: string := "1"
       );
       PORT (a_0: OUT STD_LOGIC
       );
    END COMPONENT;

    COMPONENT u7 IS
       GENERIC (A: string := "0";
            B: string := "12"
       );
       PORT (a_0: OUT STD_LOGIC
       );
    END COMPONENT;

BEGIN
    u0_inst: COMPONENT ExcludedUnit
        PORT MAP (a => sig_u0_a
        );

    u1_inst: COMPONENT ExcludedUnit
        PORT MAP (a => sig_u1_a
        );

    u2_inst: COMPONENT OnceUnit
        PORT MAP (a => sig_u2_a
        );

    u3_inst: COMPONENT OnceUnit
        PORT MAP (a => sig_u3_a
        );

    u4_inst: COMPONENT OnceUnit
        PORT MAP (a => sig_u4_a
        );

    u5_inst: COMPONENT u5
        GENERIC MAP (A => "0",
            B => "1"
        )
        PORT MAP (a_0 => sig_u5_a_0
        );

    u6_inst: COMPONENT u5
        GENERIC MAP (A => "0",
            B => "1"
        )
        PORT MAP (a_0 => sig_u6_a_0
        );

    u7_inst: COMPONENT u7
        GENERIC MAP (A => "0",
            B => "12"
        )
        PORT MAP (a_0 => sig_u7_a_0
        );

    a <= sig_u0_a & sig_u1_a & sig_u2_a & sig_u3_a & sig_u4_a & sig_u5_a_0 & sig_u6_a_0;
END ARCHITECTURE;"""


class SerializerModes_TC(unittest.TestCase):
    def test_all(self):
        s = toRtl(ExampleA())
        self.assertEqual(s, expected_vhdl)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(TransTmpl_TC('test_walkFlatten_arr'))
    suite.addTest(unittest.makeSuite(SerializerModes_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)