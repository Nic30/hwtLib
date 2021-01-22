#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import ceil

from hwt.code import FsmBuilder, If, Switch
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.enum import HEnum
from hwt.interfaces.std import Handshaked, HandshakeSync, Signal, VectSignal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwtLib.clocking.clkBuilder import ClkBuilder
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.handshaked.storedBurst import HandshakedStoredBurst
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.peripheral.displays.hd44780.intf import Hd44780Intf


class Hd44780CmdIntf(HandshakeSync):
    """
    .. hwt-autodoc::
    """
    def _config(self):
        self.DATA_WIDTH = Param(8)

    def _declr(self):
        self.rs = Signal()  # register select
        self.rw = Signal()
        self.long_wait = Signal()
        self.d = VectSignal(self.DATA_WIDTH)
        super(Hd44780CmdIntf, self)._declr()


class Hd44780CmdIntfBurst(HandshakedStoredBurst):
    """
    .. hwt-autodoc::
    """

    def __init__(self):
        super(Hd44780CmdIntfBurst, self).__init__(Hd44780CmdIntf)
        self.DATA = ((0, 0, 0, 0), # an example meaningless data
                     (0, 0, 0, 1))

    def set_data(self, intf: Hd44780CmdIntf, d):
        if d is None:
            rs, rw, long_wait, d = None, None, None, None
        else:
            rs, rw, long_wait, d = d
        return [
            intf.rs(rs),
            intf.rw(rw),
            intf.long_wait(long_wait),
            intf.d(d),
        ]


# http://elm-chan.org/docs/lcd/hd44780_e.html
class Hd44780Driver(Unit):
    """
    Controller for Hitachi HD44780 based LCD displays

    * Manages command delays and IO control
    * Sends initialization sequence
    * Translates '\\n' to a jump on next line and clean of line
    * Translates '\\f' to a clean the display and set cursor
        to first line first char

    :attention: The character set of HD44780 is not ASCII,
        but it is very similar

    .. hwt-autodoc::
    """

    def _config(self):
        self.LCD_ROWS = Param(2)
        self.LCD_COLS = Param(16)
        self.LCD_DATA_WIDTH = Param(8)
        self.LCD_FREQ = Param(int(270e3))
        # frequency of this component to compute timing for LCD control
        self.FREQ = Param(int(100e6))

    def _declr(self):
        addClkRstn(self)
        self.clk.FREQ = self.FREQ
        with self._paramsShared(prefix="LCD_"):
            self.dataOut = Hd44780Intf()._m()
        self.dataIn = Handshaked()
        self.dataIn.DATA_WIDTH = 8

    def _translate_data_in(self, din: Handshaked) -> Hd44780CmdIntf:
        """
        Translates special characters to a LCD commands

        * '\\n' jump on next line and clean it with ' '
        * '\\f' clean the LCD and reset cursor position
        """
        if self.LCD_ROWS > 1:
            row = self._reg('row', Bits(log2ceil(self.LCD_ROWS - 1)), def_val=0)
            line_offsets = self._sig("line_offsets", Bits(8)[self.LCD_ROWS], def_val=[
                Hd44780Intf.CMD_DDRAM_ADDR_SET(i * self.LCD_COLS)
                for i in range(self.LCD_ROWS)
            ])
            line_offset = self._sig("line_offset", Bits(8))
            line_offset(line_offsets[row])
        else:
            # version without row register
            raise NotImplementedError()

        col = self._reg('col', Bits(log2ceil(self.LCD_COLS - 1)), def_val=0)

        dout = Hd44780CmdIntf()
        dout.DATA_WIDTH = self.LCD_DATA_WIDTH
        self.data_in_translated = dout

        new_line_fsm_t = HEnum("new_line_fsm_t", [
            'row_incr',
            'jmp_on_nextline',
            "clean_line",
            "jmp_on_line_start",
        ])
        new_line_fsm = FsmBuilder(self, new_line_fsm_t, "new_line_fsm")\
            .Trans(new_line_fsm_t.row_incr, (din.vld & din.data._eq(ord('\n')),
                                             new_line_fsm_t.jmp_on_nextline))\
            .Trans(new_line_fsm_t.jmp_on_nextline, (dout.rd,
                                                    new_line_fsm_t.clean_line))\
            .Trans(new_line_fsm_t.clean_line, (dout.rd & col._eq(self.LCD_COLS - 1),
                                               new_line_fsm_t.jmp_on_line_start))\
            .Trans(new_line_fsm_t.jmp_on_line_start, (dout.rd,
                                                      new_line_fsm_t.row_incr)).stateReg

        def set_out(d, rs, rw, long_wait):
            return [
                dout.d(d),
                dout.rs(rs),
                dout.rw(rw),
                dout.long_wait(long_wait),
            ]

        If(din.vld & din.data._eq(ord('\n')),
            # jump on next line and clean it with ' ' and jump back on first char
            Switch(new_line_fsm)\
            .Case(new_line_fsm_t.row_incr,
                row(row + 1),
                *set_out(None, None, None, None),
                din.rd(0),
                dout.vld(0),
            ).Case(new_line_fsm_t.jmp_on_nextline,
                col(0),
                *set_out(line_offset,
                         Hd44780Intf.RS_CONTROL,
                         Hd44780Intf.RW_WRITE, 0),
                din.rd(0),
                dout.vld(1),
            ).Case(new_line_fsm_t.clean_line,
                If(dout.rd,
                   col(col + 1),
                ),
                *set_out(Hd44780Intf.CHAR_MAP[' '],
                         Hd44780Intf.RS_DATA,
                         Hd44780Intf.RW_WRITE, 0),
            ).Case(new_line_fsm_t.jmp_on_line_start,
                *set_out(line_offset,
                         Hd44780Intf.RS_CONTROL,
                         Hd44780Intf.RW_WRITE, 0),
                *StreamNode([din], [dout]).sync(),
            ),
        ).Elif(din.vld & din.data._eq(ord('\f')),
            *set_out(Hd44780Intf.CMD_CLEAR_DISPLAY,
                     Hd44780Intf.RS_CONTROL,
                     Hd44780Intf.RW_WRITE, 1),
            *StreamNode([din], [dout]).sync(),
        ).Else(
            *set_out(din.data,
                     Hd44780Intf.RS_DATA,
                     Hd44780Intf.RW_WRITE, 0),
            *StreamNode([din], [dout]).sync(),
        )

        return dout

    def _io_core(
            self, data_in: Hd44780CmdIntf,
            cmd_timer_rst,
            lcd_clk_en: RtlSignal,
            delay_cmd_half_done: RtlSignal,
            delay_cmd_done: RtlSignal,
            delay_cmd_long_done: RtlSignal):
        st_t = HEnum("st_t", [
            "init_delay_after_powerup",
            "idle",
            "write",  # cmd/data
        ])
        is_long_cmd = self._reg("is_long_cmd")
        st = FsmBuilder(self, st_t, "st")\
            .Trans(st_t.init_delay_after_powerup, (delay_cmd_long_done, st_t.idle))\
            .Trans(st_t.idle, (data_in.vld, st_t.write))\
            .Trans(st_t.write, ((is_long_cmd & delay_cmd_long_done) |
                                (~is_long_cmd & delay_cmd_done), st_t.idle))\
            .stateReg
        cmd_timer_rst(st._eq(st_t.idle))

        data_in.rd(st._eq(st_t.write) & ((delay_cmd_done & ~is_long_cmd) |
                                         (delay_cmd_long_done & is_long_cmd)))

        data_out = self.dataOut
        data_out.d(data_in.d)
        data_out.rw(data_in.rw)
        data_out.rs(data_in.rs)

        en_in_first_half_period = self._reg("en_in_first_half_period", def_val=1)
        If(st._eq(st_t.idle),
            is_long_cmd(data_in.long_wait),
            en_in_first_half_period(1),
        ).Elif(en_in_first_half_period & delay_cmd_half_done,
            en_in_first_half_period(0),
        )

        en_delay = self._reg("en_delay", def_val=0)
        If(lcd_clk_en,
           en_delay((st != st_t.idle) & en_in_first_half_period)
        )
        data_out.en(en_delay)

    def _impl(self):
        """
        * read on 'en' faling edge, write on 'en' rising edge
        * 'en' max frequency = LCD_FREQ / 10
        * rs has to be set at least 1 clk (LCD_FREQ) before rising edge of 'en'
        """
        LCD_DW = self.LCD_DATA_WIDTH
        assert LCD_DW in (4, 8), LCD_DW
        cmd_timer_rst = self._sig("cmd_timer_rst")
        HALF_LCD_PERIOD = ceil(self.FREQ / (self.LCD_FREQ * 2))
        LCD_CLK_PER = 2 * HALF_LCD_PERIOD
        lcd_clk_en, = ClkBuilder(self, self.clk).timers([
            ("lcd_clk_en", LCD_CLK_PER),
        ])
        delay_cmd_half_done, delay_cmd_done, delay_cmd_long_done =\
            ClkBuilder(self, self.clk)\
            .timers([
                # used to signalize that the 'en' should be asserted low
                ("delay_cmd_half_done", Hd44780Intf.DELAY_CMD // 2),
                # used to signalize that the processing of command is completed
                ("delay_cmd_done", Hd44780Intf.DELAY_CMD),
                # used to signalize that the long command (return home, etc.) is completed
                ("delay_cmd_long_done", Hd44780Intf.DELAY_RETURN_HOME)
            ],
                enableSig=lcd_clk_en,
                rstSig=cmd_timer_rst
            )
        data_in_tmp = Hd44780CmdIntf()
        data_in_tmp.DATA_WIDTH = self.LCD_DATA_WIDTH
        self.data_in_tmp = data_in_tmp

        self._io_core(data_in_tmp, cmd_timer_rst,
                      lcd_clk_en, delay_cmd_half_done,
                      delay_cmd_done, delay_cmd_long_done)
        INIT_SEQUENCE = [
            Hd44780Intf.CMD_FUNCTION_SET(
                Hd44780Intf.DATA_LEN_8b if LCD_DW == 8 else Hd44780Intf.DATA_LEN_4b,
                self.LCD_ROWS - 1,
                Hd44780Intf.FONT_5x8),
            Hd44780Intf.CMD_DISPLAY_CONTROL(1, 0, 0),
            Hd44780Intf.CMD_ENTRY_MODE_SET(1, 1),
        ]
        init_seq = Hd44780CmdIntfBurst()
        init_seq.DATA_WIDTH = self.LCD_DATA_WIDTH
        init_seq.DATA = tuple(
            (Hd44780Intf.RS_CONTROL, Hd44780Intf.RW_WRITE, 0, d)
            for d in INIT_SEQUENCE
        )
        self.init_seq = init_seq
        propagateClkRstn(self)
        data_in = self._translate_data_in(self.dataIn)
        data_in_tmp(HsBuilder.join_prioritized(self, [init_seq.dataOut, data_in]).end)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = Hd44780Driver()
    print(to_rtl_str(u))
