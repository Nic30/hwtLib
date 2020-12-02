from enum import Enum
from pyMathBitPrecise.bit_utils import set_bit_range

# deassign_xyz_mux;
ARITHMETIC_MODES_DRC_deassign_xyz_mux = [
    # 0bxxx0101010
    * [set_bit_range(0b0000101010, 7, 3, i) for i in range(8)],
    0b0000000000,
    0b0000011000,
    0b0000011010,
    0b0000101000,
    0b0001000000,
    0b0001011000,
    0b0001011010,
    0b0001100000,
    0b0001100010,
    0b0001111000,
    0b0001111010,
    0b0010000000,
    0b0010011000,
    0b0010011001,
    0b0010011011,
    0b0010101000,
    0b0010101001,
    0b0010101011,
    0b0010101110,
    0b0011000000,
    0b0011011000,
    0b0011011001,
    0b0011011011,
    0b0011100000,
    0b0011100001,
    0b0011100011,
    0b0011100100,
    0b0011111000,
    0b0011111001,
    0b0011111011,
    0b0110000000,
    0b0110000010,
    0b0110011000,
    0b0110011010,
    0b0110101000,
    0b0110101110,
    0b0111000000,
    0b0111000010,
    0b0111011000,
    0b0111100000,
    0b0111100010,
    0b0111111000,
    0b1010000000,
    0b1010011000,
    0b1010011001,
    0b1010011011,
    0b1010101000,
    0b1010101001,
    0b1010101011,
    0b1010101110,
    0b1011000000,
    0b1011011000,
    0b1011011001,
    0b1011011011,
    0b1011100000,
    0b1011100001,
    0b1011100011,
    0b1011111000,
    0b1011111001,
    0b1011111011,
]

# if (PREG != 1) display_invalid_opmode; else deassign_xyz_mux;
ARITHMETIC_MODES_DRC_deassign_xyz_mux_if_PREG_eq_1 = [
    0b0000010000,
    0b0000010010,
    0b0000011100,
    0b0001010000,
    0b0001010010,
    0b0001011100,
    0b0001100100,
    0b0001110000,
    0b0001110010,
    0b0001110101,
    0b0001110111,
    0b0001111100,
    0b0010010000,
    0b0010010101,
    0b0010010111,
    0b0011010000,
    0b0011010101,
    0b0011010111,
    0b0011110000,
    0b0011110101,
    0b0011110111,
    0b0011110001,
    0b0011110011,
    0b0100000000,
    0b0100000010,
    0b0100010000,
    0b0100010010,
    0b0100011000,
    0b0100011010,
    0b0100011101,
    0b0100011111,
    0b0100101000,
    0b0100101101,
    0b0100101111,
    0b0101000000,
    0b0101000010,
    0b0101010000,
    0b0101011000,
    0b0101011101,
    0b0101011111,
    0b0101100000,
    0b0101100010,
    0b0101100101,
    0b0101100111,
    0b0101110000,
    0b0101110101,
    0b0101110111,
    0b0101111000,
    0b0101111101,
    0b0101111111,
    0b0110000100,
    0b0110010000,
    0b0110010010,
    0b0110010101,
    0b0110010111,
    0b0110011100,
    0b0111000100,
    0b0111010000,
    0b0111010101,
    0b0111010111,
    0b0111110000,
    0b1001000010,
    0b1010010000,
    0b1010010101,
    0b1010010111,
    0b1011010000,
    0b1011010101,
    0b1011010111,
    0b1011110000,
    0b1011110101,
    0b1011110111,
    0b1011110001,
    0b1011110011,
    0b1100000000,
    0b1100010000,
    0b1100011000,
    0b1100011101,
    0b1100011111,
    0b1100101000,
    0b1100101101,
    0b1100101111,
    0b1101000000,
    0b1101010000,
    0b1101011000,
    0b1101011101,
    0b1101011111,
    0b1101100000,
    0b1101100101,
    0b1101100111,
    0b1101110000,
    0b1101110101,
    0b1101110111,
    0b1101111000,
    0b1101111101,
    0b1101111111,
]

LOGIC_MODES_DRC_deassign_xyz_mux = [
    0b0000000,
    0b0000011,
    0b0010000,
    0b0010011,
    0b0110000,
    0b0110011,
    0b1010000,
    0b1010011,
    0b0001000,
    0b0001011,
    0b0011000,
    0b0011011,
    0b0111000,
    0b0111011,
    0b1011000,
    0b1011011,
]
LOGIC_MODES_DRC_deassign_xyz_mux_if_PREG_eq_1 = [
    0b0000010,
    0b0010010,
    0b0100000,
    0b0100010,
    0b0100011,
    0b0110010,
    0b1010010,
    0b1100000,
    0b1100010,
    0b1100011,
    0b0001010,
    0b0011010,
    0b0101000,
    0b0101010,
    0b0101011,
    0b0111010,
    0b1011010,
    0b1101000,
    0b1101010,
    0b1101011,
]


class X_SEL(Enum):
    ZERO = 0b000_00_00
    M = 0b000_01_01
    P = 0b000_00_10  # Must select with PREG = 1
    A_B = 0b000_00_11  # 48 bits wide


class Y_SEL(Enum):
    ZERO = 0b000_00_00
    M = 0b000_01_01
    # Used mainly for logic unit
    # bitwise operations on the X and
    # Z multiplexers
    MINUS_1 = 0b000_10_00
    C = 0b000_11_00


class Z_SEL(Enum):
    ZERO = 0b000_00_00
    PCIN = 0b001_00_00
    P = 0b010_00_00  # Must select with PREG = 1
    C = 0b011_00_00
    P_MACC = 0b100_10_00  # Use for MACC extend only. Must select with PREG = 1
    PCIN_SHIFT_17b = 0b101_00_00
    P_SHIFT_17b = 0b110_00_00  # Must select with PREG = 1


def get_opmode(x: X_SEL, y: Y_SEL, z: Z_SEL):
    if x == X_SEL.M:
        assert y == Y_SEL.M
    elif y == Y_SEL.M:
        assert x == X_SEL.M
    if z == Z_SEL.P_MACC:
        assert x == X_SEL.ZERO
        assert y == Y_SEL.MINUS_1

    return (z.value | y.value | x.value)


ALU_MODE = {
    "Z + X + Y + CIN": 0b0000,
    "Z - (X + Y + CIN)": 0b0011,
    # In two’s complement: -Z = ~Z + 1
    "-Z + (X + Y + CIN) - 1": 0b0001,
    "-Z - X - Y - CIN - 1": 0b0010,

    "X ^ Z": (Y_SEL.ZERO, 0b0100),
    "~(X ^ Z)": (Y_SEL.ZERO, 0b0101), # xnor
    "X & Z": (Y_SEL.ZERO, 0b1100),
    "X & ~Z": (Y_SEL.ZERO, 0b1101),
    "~(X & Z)": (Y_SEL.ZERO, 0b1110),
    "~X | Z": (Y_SEL.ZERO, 0b1111),

    "X | Z": (Y_SEL.MINUS_1, 0b1100),
    "X | ~Z": (Y_SEL.MINUS_1, 0b1101),
    "~(X | Z)": (Y_SEL.MINUS_1, 0b1110), # nor
    "~X & Z": (Y_SEL.MINUS_1, 0b1111)
}


class CARRYIN_SEL(Enum):
    CARRYIN = 0b000  # General interconnect
    PCIN_47_n = 0b001  # Rounding PCIN (round towards infinity)
    CARRYCASCIN = 0b010  # Larger add/sub/acc (parallel operation)
    PCIN_47 = 0b011  # Rounding PCIN (round towards zero)
    # For larger add/sub/acc (sequential
    # operation via internal feedback). Must select
    # with PREG = 1
    CARRYCASCOUT = 0b100
    P_47_n = 0b101  # Rounding P (round towards infinity). Must select with PREG = 1
    A_27_eq_B_17 = 0b110  # Rounding A x B
    P_47 = 0b111  # For rounding P (round towards zero). Must select with PREG = 1


class MUL_A_SEL(Enum):
    (
        A2,
        A1,
        ZERO,
        D_PLUS_A2,
        D_PLUS_A1,
        D,
        MINUS_A2,
        MINUS_A1,
        D_MINUS_A2,
        D_MINUS_A1
    ) = range(10)


class MUL_B_SEL(Enum):
    B2 = 0
    B1 = 1


_inmode_with_not_use_dport = {
    MUL_A_SEL.A2: 0b0000,
    MUL_A_SEL.A1: 0b0001,
    MUL_A_SEL.ZERO: 0b0010,
}

_inmode_with_use_dport = {
   **_inmode_with_not_use_dport,
   MUL_A_SEL.D_PLUS_A2: 0b0100,
   MUL_A_SEL.D_PLUS_A1: 0b0101,
   MUL_A_SEL.D: 0b0110,
   MUL_A_SEL.MINUS_A2: 0b1000,
   MUL_A_SEL.MINUS_A1: 0b1001,
   MUL_A_SEL.D_MINUS_A2: 0b1100,
   MUL_A_SEL.D_MINUS_A1: 0b1101,
}


def get_inmode(AREG: int, USE_DPORT: bool, mul_a_sel: MUL_A_SEL, mul_b_sel: MUL_B_SEL):
    assert AREG in [0, 1, 2], AREG
    if USE_DPORT:
        v = _inmode_with_not_use_dport[mul_a_sel]
    else:
        v = _inmode_with_use_dport[mul_a_sel]

    return (mul_b_sel.value << 3 | v)
