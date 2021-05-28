#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Switch, Concat
from hwt.code_utils import rename_signal
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.enum import HEnum
from hwt.interfaces.utils import propagateClkRst, addClkRst
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwtLib.peripheral.usb.usb2.ulpi import Ulpi, ULPI_TX_CMD, ULPI_REG, \
    ulpi_reg_function_control_t, ulpi_reg_function_control_t_reset_default, \
    ulpi_reg_otg_control_t, ulpi_reg_otg_control_t_reset_defaults, \
    ulpi_reg_usb_interrupt_status_t_reset_default
from hwtLib.peripheral.usb.usb2.utmi import Utmi_8b, utmi_interrupt_t
from pyMathBitPrecise.bit_utils import mask


class Utmi_to_Ulpi(Unit):
    """
    The ULPI is an interface which reduces the number of signals for UTMI+ interface.
    This reduction is done using a register file which drives signals which are not used
    and bi-directional wiring. This component does translation of ULPI to UTMI+ by keeping copy of UTMI+
    registers and synchronizing the changes and it also handles the drive of the bi-directional wires.

    :note: For up to UTMI+ Level 3

    Based on https://raw.githubusercontent.com/ultraembedded/core_ulpi_wrapper/3c202963ac4b4ae50cadb44ce79c11463d3c6484/src_v/ulpi_wrapper.v

    .. hwt-autodoc::
    """

    def _declr(self):
        addClkRst(self)
        # PHY is a master for UTMI/ULPI style interface
        self.utmi = Utmi_8b()._m()
        self.ulpi = Ulpi()

    def ulpi_turnaround_detect(self, ulpi_dir: RtlSignal):
        #-----------------------------------------------------------------
        # Bus turnaround detect
        #-----------------------------------------------------------------
        ulpi_dir_q = self._reg("ulpi_dir_q", def_val=1)
        ulpi_dir_q(ulpi_dir)
        turnaround_w = rename_signal(self, ulpi_dir_q != ulpi_dir._eq(Ulpi.DIR.PHY), "turnaround_w")
        return turnaround_w

    @staticmethod
    def parse_RX_CMD(ulpi_data, utmi_linestate_q, utmi_interrupt_q, utmi_rxactive_q, utmi_rxerror_q):
        return [
            utmi_linestate_q(ulpi_data[2:0]),
            Switch(ulpi_data[4:2])\
            .Case(0b00,
                  utmi_interrupt_q.SessEnd(1),
                  utmi_interrupt_q.SessValid(0),
                  utmi_interrupt_q.VbusValid(0),
            ).Case(0b01,
                  utmi_interrupt_q.SessEnd(0),
                  utmi_interrupt_q.SessValid(0),
                  utmi_interrupt_q.VbusValid(0),
            ).Case(0b10,
                  utmi_interrupt_q.SessValid(1),
                  utmi_interrupt_q.VbusValid(0),
            ).Case(0b11,
                  utmi_interrupt_q.VbusValid(1),
            ),
            Switch(ulpi_data[6:4])\
            .Case(0b00,
                utmi_rxactive_q(0),
                utmi_rxerror_q(0)
            ).Case(0b01,
                utmi_rxactive_q(1),
                utmi_rxerror_q(0)
            ).Case(0b10,
                utmi_interrupt_q.HostDisconnect(1)
            ).Case(0b11,
                utmi_rxactive_q(1),
                utmi_rxerror_q(1)
            ),
            utmi_interrupt_q.IdGnd(ulpi_data[6])
        ]

    def _impl(self):
        ulpi: Ulpi = self.ulpi
        utmi: Utmi_8b = self.utmi

        # Description:
        #  - Converts from UTMI interface to reduced pin count ULPI.
        #  - No support for low power mode.
        #  - I/O synchronous to 60MHz ULPI clock input (from PHY)
        #  - Tested against SMSC/Microchip USB3300 in device mode.
        #-----------------------------------------------------------------
        # States
        #-----------------------------------------------------------------
        state_t = HEnum("state_t", ["w", "idle", "cmd", "data", "reg"])
        state_q = self._reg("state_q", dtype=state_t, def_val=state_t.idle)
        #-----------------------------------------------------------------
        # UTMI Mode Select
        #-----------------------------------------------------------------
        # flag which tells that the function mode register is now ready writen to PHY
        mode_update_q = self._reg("mode_update_q", def_val=0)

        function_control_q = self._reg("function_control_q", ulpi_reg_function_control_t,
                                       def_val=ulpi_reg_function_control_t_reset_default)
        mode_write_q = self._reg("mode_write_q", def_val=0)
        # Detect register write completion
        mode_complete_w = rename_signal(self, ((state_q._eq(state_t.reg) & mode_write_q) & ulpi.nxt) & ulpi.dir._eq(Ulpi.DIR.LINK), "mode_complete_w")
        #-----------------------------------------------------------------
        # UTMI OTG Control
        #-----------------------------------------------------------------
        otg_update_q = self._reg("otg_update_q", def_val=0)
        otg_control_q = self._reg("otg_control_q", ulpi_reg_otg_control_t,
                                  def_val=ulpi_reg_otg_control_t_reset_defaults)
        otg_write_q = self._reg("otg_write_q", def_val=0)
        # Detect register write completion
        otg_complete_w = rename_signal(self, ((state_q._eq(state_t.reg) & otg_write_q) & ulpi.nxt) & ulpi.dir._eq(Ulpi.DIR.LINK), "otg_complete_w")

        #-----------------------------------------------------------------
        # Tx Buffer - decouple UTMI Tx from PHY I/O
        #-----------------------------------------------------------------
        # tx_fifo = HandshakedFifo(Handshaked)
        # tx_fifo.DATA_WIDTH = 8
        # tx_fifo.DEPTH = 2
        # self.tx_fifo = tx_fifo

        #-----------------------------------------------------------------
        # Implementation
        #-----------------------------------------------------------------
        # Xilinx placement pragmas:
        # synthesis attribute IOB of ulpi_data_q is "TRUE"
        # synthesis attribute IOB of ulpi_stp_q is "TRUE"
        ulpi_data_q = self._reg("ulpi_data_q", Bits(8), def_val=0)
        ulpi_stp_q = self._reg("ulpi_stp_q", def_val=0)
        data_q = self._reg("data_q", Bits(8), def_val=0)
        utmi_rxvalid_q = self._reg("utmi_rxvalid_q", def_val=0)
        utmi_rxerror_q = self._reg("utmi_rxerror_q", def_val=0)
        utmi_rxactive_q = self._reg("utmi_rxactive_q", def_val=0)
        utmi_linestate_q = self._reg("utmi_linestate_q", Bits(2), def_val=0)
        utmi_data_q = self._reg("utmi_data_q", Bits(8), def_val=0)

        # interupts are cleared once new RX CMD is recieved and it does not contain the event flag
        utmi_interrupt_q = self._reg("utmi_interrupt_q", utmi_interrupt_t,
                                     def_val=ulpi_reg_usb_interrupt_status_t_reset_default)
        utmi.interrupt(utmi_interrupt_q)

        # Not interrupted by a Rx
        function_control_q(utmi.function_control, exclude=[function_control_q.Reset])
        If(mode_update_q & mode_complete_w,
            function_control_q.Reset(0)
        ).Else(
            function_control_q.Reset(utmi.function_control.Reset)
        )

        If(mode_update_q & mode_complete_w,
            mode_update_q(0),
        ).Elif((function_control_q != utmi.function_control) | utmi.function_control.Reset,
            mode_update_q(1)
        )

        # Not interrupted by a Rx
        otg_control_q(utmi.otg_control)
        If(otg_update_q & otg_complete_w,
            otg_update_q(0)
        ).Elif(otg_control_q != utmi.otg_control,
            otg_update_q(1)
        )

        turnaround_w = self.ulpi_turnaround_detect(ulpi.dir)

        # utmi_tx_to_ulpi_vld = tx_fifo.dataOut.vld

        # Push
        # tx_fifo.dataIn.vld(utmi.tx.vld & utmi.tx.rd)
        # tx_fifo.dataIn.data(utmi.tx.data)

        # Pop
        # tx_fifo.dataOut.rd(utmi_tx_to_ulpi_vld & utmi_tx_accept_w)
        # utmi.tx.rd(tx_fifo.dataIn.rd & tx_delay_complete_w)
        utmi_tx_to_ulpi_vld = utmi.tx.vld
        utmi_tx_data_w = utmi.tx.data

        utmi_tx_accept_w = rename_signal(
            self,
            ~turnaround_w & ulpi.dir._eq(Ulpi.DIR.LINK) & (
                (state_q._eq(state_t.idle) & ~(mode_update_q | otg_update_q | turnaround_w)) |
                (state_q._eq(state_t.data) & ulpi.nxt)
            ),
            "utmi_tx_accept_w")
        utmi.tx.rd(utmi_tx_accept_w)

        ulpi_stp_q(~turnaround_w & ulpi.dir._eq(Ulpi.DIR.LINK) & ulpi.nxt &
            (state_q._eq(state_t.reg) |
             (state_q._eq(state_t.data) & ~utmi_tx_to_ulpi_vld)
            )
        )
        utmi_rxvalid_q(~turnaround_w & ulpi.dir._eq(Ulpi.DIR.PHY) & ulpi.nxt)
        If(turnaround_w,
            If(ulpi.dir._eq(Ulpi.DIR.PHY) & ulpi.nxt,
                # Turnaround: Input + NXT - set RX_ACTIVE
                utmi_rxactive_q(1),
                # Register write - abort
                If(state_q._eq(state_t.reg),
                    state_q(state_t.idle),
                    ulpi_data_q(0),
                )
            ).Elif(ulpi.dir._eq(Ulpi.DIR.LINK),
                utmi_rxactive_q(0),
                # Register write - abort
                If(state_q._eq(state_t.reg),
                    state_q(state_t.idle),
                    ulpi_data_q(0),
                )
            )
        ).Else(
            If(ulpi.dir._eq(Ulpi.DIR.PHY),
                If(ulpi.nxt,
                    #-----------------------------------------------------------------
                    # Input: RX_DATA
                    #-----------------------------------------------------------------
                    utmi_rxactive_q(1),
                    utmi_data_q(ulpi.data.i)
                ).Else(
                    #-----------------------------------------------------------------
                    # Input: RX_CMD (phy status), decode encoded status/event bits from this byte
                    #-----------------------------------------------------------------
                    self.parse_RX_CMD(ulpi.data.i,
                        utmi_linestate_q, utmi_interrupt_q,
                        utmi_rxactive_q, utmi_rxerror_q)
                )
            ).Else(
                #-----------------------------------------------------------------
                # Output
                #-----------------------------------------------------------------
                If(state_q._eq(state_t.idle),
                    If(mode_update_q,
                        # IDLE: Pending mode update
                        state_q(state_t.cmd),
                        ulpi_data_q(ULPI_TX_CMD.REGW(ULPI_REG.Function_Control)),
                        data_q(function_control_q._reinterpret_cast(data_q._dtype) & mask(7)),
                        otg_write_q(0),
                        mode_write_q(1),
                    ).Elif(otg_update_q,
                        # IDLE: Pending OTG control update
                        state_q(state_t.cmd),
                        ulpi_data_q(ULPI_TX_CMD.REGW(ULPI_REG.OTG_Control)),
                        data_q(otg_control_q._reinterpret_cast(data_q._dtype)),
                        otg_write_q(1),
                        mode_write_q(0),
                    ).Elif(utmi_tx_to_ulpi_vld,
                        # IDLE: Pending transmit
                        # data should have USB_PID header and this is just to be sure
                        ulpi_data_q(ULPI_TX_CMD.USB_PID(utmi_tx_data_w[4:0])),
                        state_q(state_t.data)
                    )
                ).Elif(ulpi.nxt,
                    If(state_q._eq(state_t.cmd),
                        # Command, Write Register
                        state_q(state_t.reg),
                        ulpi_data_q(data_q),
                    ).Elif(state_q._eq(state_t.reg),
                        # Data (register write)
                        state_q(state_t.idle),
                        ulpi_data_q(0),
                        otg_write_q(0),
                        mode_write_q(0),
                    ).Elif(state_q._eq(state_t.data),
                        # Data
                        If(utmi_tx_to_ulpi_vld,
                            state_q(state_t.data),
                            ulpi_data_q(utmi_tx_data_w),
                        ).Else(
                            # End of packet
                            state_q(state_t.idle),
                            ulpi_data_q(0),
                        )
                    )
                )
            )
        )

        ulpi.data.o(ulpi_data_q)
        ulpi.data.t(Concat(*(utmi_tx_accept_w for _ in range(8))))
        ulpi.stp(ulpi_stp_q)
        utmi.LineState(utmi_linestate_q)
        utmi.rx.data(utmi_data_q)
        utmi.rx.error(utmi_rxerror_q)
        utmi.rx.active(utmi_rxactive_q)
        utmi.rx.valid(utmi_rxvalid_q)

        propagateClkRst(self)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = Utmi_to_Ulpi()
    print(to_rtl_str(u))
