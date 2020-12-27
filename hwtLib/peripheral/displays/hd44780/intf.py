# -*- coding: utf-8 -*-

from math import ceil

from hwt.interfaces.std import Signal, VectSignal
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from pyMathBitPrecise.bit_utils import get_bit, mask, get_bit_range
from hwtSimApi.agents.base import AgentBase
from hwtSimApi.hdlSimulator import HdlSimulator
from hwtSimApi.triggers import WaitTimeslotEnd, Edge


class Hd44780Intf(Interface):
    """
    HD44780 is an old but comonly used driver for character LCDs.
    It is commonly used for 16x2 character displays but does also supports
    a different number of characters.

    :note: if DATA_WIDTH == 4 the .d signal has 4bits and its bits
        whould be connected to bits 7-4 on physical device

    .. hwt-autodoc::
    """

    # for f_osc = 270KHz, which is deaut clock used by most of the LCDs
    # 37 us, dealy or rest of the commands
    DELAY_CMD = 10
    # 1.52 ms, also for clear display command
    DELAY_RETURN_HOME = 41 * DELAY_CMD
    # ROM code: A00
    CHAR_MAP = {
        **{chr(c): c for c in range(ord(' '), ord('}') + 1)},
        **{
            '¥': 0b01011100,  # replaces \\ glyph in ASCII range ablowe
            '←': 0b01111110,
            '→': 0b01111111,
            # 'ヲ': 0b10100110,
            '⌜': 0b10100010,
            '⌟': 0b10100011,
            # maybe not exactly \\ but looks very similar and there is nothing
            # like \\
            '\\': 0b10100100,
            '·': 0b10100101,

            '°': 0b11011111,
            'α': 0b11100000,
            'ä': 0b11100001,
            'β': 0b11100010,
            'ε': 0b11100011,
            'μ': 0b11100100,
            'σ': 0b11100101,
            'ρ': 0b11100111,

            '√': 0b11101000,

            '¢': 0b11101100,
            'Ⱡ': 0b11101101,
            'ñ': 0b11101110,
            'ö': 0b11101111,

            'θ': 0b11110010,
            '∞': 0b11110011,
            'Ω': 0b11110100,
            'ü': 0b11110101,
            'Σ': 0b11110110,
            'π': 0b11110111,
            'x̅': 0b11110000,

            '÷': 0b11101011,

            '█': 0b11111111,
        },
    }
    INCR = 1
    DECR = 0
    SC_DISPLAY_SHIFT = 1
    SC_CURSOR_MOVE = 0
    SHIFT_RIGHT = 1
    SHIFT_LEFT = 0
    BUSSY = 1
    RS_CONTROL = 0
    RS_DATA = 1
    RW_READ = 1
    RW_WRITE = 0

    CMD_CLEAR_DISPLAY = 1  # (long command)
    CMD_RETURN_HOME = 2  # (long command)

    @staticmethod
    def CMD_ENTRY_MODE_SET(incr_decr: int, shift_en: int):
        """
        speciies how the cursor should be modified after char write
        """
        return 0b00000100 | (incr_decr << 1) | (shift_en)

    @staticmethod
    def CMD_DISPLAY_CONTROL(display_on_off, cursor_on_off, cursor_blink):
        return 0b00001000 | (display_on_off << 2)\
             | (cursor_on_off << 1) | cursor_blink

    @staticmethod
    def CMD_CURSOR_OR_DISPLAY_SHIFT(shift_or_cursor, right_left):
        return 0b00010000 | (shift_or_cursor << 3) | (right_left << 2)

    # depends on physical wires
    DATA_LEN_4b = 0
    DATA_LEN_8b = 1
    # depens on LCD type
    LINES_1 = 0
    LINES_2 = 1
    FONT_5x8 = 0  # deault
    FONT_5x10 = 1

    @staticmethod
    def CMD_FUNCTION_SET(data_len, lines, font):
        assert data_len in (Hd44780Intf.DATA_LEN_4b, Hd44780Intf.DATA_LEN_8b)
        assert lines in (Hd44780Intf.LINES_1, Hd44780Intf.LINES_2)
        assert font in (Hd44780Intf.FONT_5x8, Hd44780Intf.FONT_5x8)
        return 0b00100000 | (data_len << 4) | (lines << 3) | (font << 2)

    @staticmethod
    def CMD_DDRAM_ADDR_SET(addr):
        """set cursor possition"""
        assert addr & mask(7) == addr, addr
        return 0b10000000 | addr

    def _config(self):
        self.FREQ = int(270e3)
        self.DATA_WIDTH = Param(8)
        self.ROWS = Param(2)
        self.COLS = Param(16)

    def _declr(self):
        self.en = Signal()
        self.rs = Signal()  # register select
        self.rw = Signal()
        self.d = VectSignal(self.DATA_WIDTH)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = HD44780InterfaceAgent(sim, self)


class HD44780InterfaceAgent(AgentBase):
    """
    Agent which emulates HD44780 LCD

    :ivar ~.screen: character present on screen
    """
    REV_CHAR_MAP = {v: k for k, v in Hd44780Intf.CHAR_MAP.items()}

    def __init__(self, sim: HdlSimulator, intf: Hd44780Intf):
        super(HD44780InterfaceAgent, self).__init__(sim, intf)
        self.screen = [
            [' ' for _ in range(intf.COLS)]
            for _ in range(intf.ROWS)
        ]
        self.busy = False
        self.cursor = [0, 0]  # left upper corner, [row, line]
        self.cursor_on = None
        self.cursor_blink = None
        self.display_on = None
        # speciies how the cursor should be modified after char write
        self.shift = None
        self.lines = None
        self.data_len = None
        self.font = None

    def get_str(self):
        return "\n".join(["".join(line) for line in self.screen])

    def monitor(self):
        i = self.intf
        while True:
            # print(self.sim.now // Time.ns)
            yield Edge(i.en)
            yield WaitTimeslotEnd()
            if i.en.read():
                rs = int(i.rs.read())
                rw = int(i.rw.read())
                d = int(i.d.read())
                if rs == Hd44780Intf.RS_CONTROL:
                    # command processing
                    if rw == Hd44780Intf.RW_WRITE:
                        if d & 0b10000000:
                            # cursor position set (DDRAM addr)
                            d = get_bit_range(d, 0, 7)
                            self.cursor[0] = ceil(d / i.COLS)
                            assert self.cursor[0] < i.ROWS, self.cursor[0]
                            self.cursor[1] = d % i.ROWS
                        elif d & 0b01000000:
                            raise NotImplementedError()
                        elif d & 0b00100000:
                            # CMD_FUNCTION_SET
                            self.data_len = get_bit(d, 4)
                            self.lines = get_bit(d, 3)
                            self.font = get_bit(d, 2)
                        elif d & 0b00010000:
                            # CMD_CURSOR_OR_DISPLAY_SHIFT
                            shift_or_cursor = get_bit(d, 3)
                            right_left = get_bit(d, 2)
                            if shift_or_cursor == Hd44780Intf.SC_CURSOR_MOVE:
                                c = self.cursor
                                if right_left == Hd44780Intf.SHIFT_RIGHT:
                                    c[1] += 1
                                    if c[1] == i.COLS:
                                        c[1] = 0
                                        c[0] += 1
                                        if c[0] == i.ROWS:
                                            c[0] = 0
                            else:
                                raise NotImplementedError()
                        elif d & 0b00001000:
                            # CMD_DISPLAY_CONTROL
                            self.display_on = get_bit(d, 2)
                            self.cursor_on = get_bit(d, 1)
                            self.cursor_blink = get_bit(d, 0)
                        elif d & 0b00000100:
                            # CMD_ENTRY_MODE_SET
                            shift_en = get_bit(d, 0)
                            incr_decr = get_bit(d, 1)
                            if shift_en:
                                self.shift = 1 if incr_decr == Hd44780Intf.INCR else -1
                            else:
                                self.shift = 0
                        elif d & Hd44780Intf.CMD_RETURN_HOME:
                            raise NotImplementedError()
                        elif d == Hd44780Intf.CMD_CLEAR_DISPLAY:
                            for line in self.screen:
                                for x in range(i.COLS):
                                    line[x] = ' '
                            self.cursor = [0, 0]
                        else:
                            raise NotImplementedError("{0:8b}".format(d))
                    else:
                        assert rw == Hd44780Intf.RW_READ, rw
                        raise NotImplementedError()
                else:
                    # data processing
                    assert rs == Hd44780Intf.RS_DATA, rs
                    if self.data_len == Hd44780Intf.DATA_LEN_8b:
                        d = int(d)
                        d = self.REV_CHAR_MAP.get(d, " ")
                        cur = self.cursor
                        self.screen[cur[0]][cur[1]] = d
                        cur[1] += self.shift
                    else:
                        raise NotImplementedError()
