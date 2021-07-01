#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional

from hwt.code import If, Switch, CodeBlock
from hwt.code_utils import rename_signal
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.enum import HEnum
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.std import VldSynced, Signal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.mainBases import RtlSignalBase
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axis import AxiStream
from hwtLib.peripheral.usb.constants import usb_addr_t, USB_PID, USB_VER, \
    usb_endp_t, usb_pid_t, USB_LINE_STATE
from hwtLib.peripheral.usb.descriptors.bundle import UsbDescriptorBundle, \
    UsbEndpointMeta
from hwtLib.peripheral.usb.usb2.device_core_interfaces import UsbEndpointInterface
from hwtLib.peripheral.usb.usb2.sie_rx import Usb2SieDeviceRx
from hwtLib.peripheral.usb.usb2.sie_tx import Usb2SieDeviceTx
from hwtLib.peripheral.usb.usb2.ulpi import ulpi_reg_otg_control_t_reset_defaults, \
    ulpi_reg_function_control_t_reset_default
from hwtLib.peripheral.usb.usb2.utmi import Utmi_8b
from hwtLib.types.ctypes import uint8_t
from pyMathBitPrecise.bit_utils import mask


class Usb2DeviceCore(Unit):
    """
    Based on USB descriptors build endpoint statemachines, speed negotiation logic,
    usb reset logic and transaction logic

    :see: https://www.beyondlogic.org/usbnutshell/usb4.shtml

    :ivar ~.phy: An interface to USB PHY which is connected to host
    :ivar ~.ep: And interface to USB endpont buffers of this device
    :ivar ~.usb_rst: output of USB reset detector
    :ivar ~.usb_speed: An interface which holds the index of the USB version
        to note which speed was negotiated.
    :ivar ~.current_usb_addr: An input signal with an address currently
        assigned for this device.
    :ivar ~.PRE_NEGOTIATED_TO: A parameter for testing purposes which can be used to
        specify the default state of the link negotiation state

    :ivar sie_rx: Serial Interface Engine for UTMI rx channel (host->device)
    :ivar sie_tx: Serial Interface Engine for UTMI tx channel (device->host)

    .. hwt-autodoc:: _example_Usb2DeviceCore
    """

    def _config(self):
        self.DESCRIPTORS: UsbDescriptorBundle = Param(None)
        self.CLK_FREQ = Param(int(60e6))
        self.PRE_NEGOTIATED_TO: Optional[USB_VER] = Param(None)

    def _declr(self):
        assert isinstance(self.DESCRIPTORS, UsbDescriptorBundle), self.DESCRIPTORS
        self.ENDPOINT_CONFIG = self.DESCRIPTORS.get_endpoint_meta()
        addClkRstn(self)
        self.clk.FREQ = self.CLK_FREQ

        self.phy = Utmi_8b()
        self.ep: UsbEndpointInterface = UsbEndpointInterface()._m()

        self.usb_rst: Signal = Signal()._m()
        self.usb_speed: VldSynced = VldSynced()._m()
        self.usb_speed.DATA_WIDTH = log2ceil(len(USB_VER.values))
        self.current_usb_addr = Signal(usb_addr_t)

        self.sie_rx = Usb2SieDeviceRx()
        self.sie_tx = Usb2SieDeviceTx()

    def detect_usb_rst(self, LineState: RtlSignal, usb_speed: VldSynced):
        se0_cntr = self._reg("se0_cntr", Bits(15), def_val=0)
        usb_rst_detected = se0_cntr[14]
        # is_negotiated_to_HS = usb_speed.vld & usb_speed.data._eq(USB_VER.values.index(USB_VER)

        # LS/FS SE0 for more than > 2.5us
        If(LineState._eq(USB_LINE_STATE.SE0),
            If(~usb_rst_detected,
               se0_cntr(se0_cntr + 1)
            )
        ).Else(
            # [TODO] HS more than 3ms of bus inactivity -> suspend or reset
            se0_cntr(0),
        )
        return usb_rst_detected

    def define_endpoint_states(self, endp: RtlSignal, rst_any:RtlSignal):
        # used for DATA0/1 toogling
        # [todo] endpoint specific
        ep_out_data_bits = []
        ep_in_data_bits = []
        for i, (ep_out, ep_in) in enumerate(self.ENDPOINT_CONFIG):
            if ep_out is not None:
                ep_out: UsbEndpointMeta
                o_b = self._reg(f"ep{i:d}_out_data_bit", BIT, def_val=0, rst=rst_any)
            else:
                o_b = None

            ep_out_data_bits.append(o_b)
            if ep_in is not None:
                ep_in: UsbEndpointMeta
                i_b = self._reg(f"ep{i:d}_in_data_bit", BIT, def_val=0, rst=rst_any)
            else:
                i_b = None
            ep_in_data_bits.append(i_b)

        ep_out_data_bit = self._sig("ep_out_data_bit")
        ep_in_data_bit = self._sig("ep_in_data_bit")
        Switch(endp)\
        .add_cases((i, [
            ep_out_data_bit(o_b),
            ep_in_data_bit(i_b),
            ]) for i, (o_b, i_b) in enumerate(zip(ep_out_data_bits, ep_in_data_bits))
        ).Default(
            ep_out_data_bit(None),
            ep_in_data_bit(None),
        )
        ep_is_isochronous = BIT.from_py(0)

        def set_ep_out_data_bit(val):
            res = []
            for i, o_b in enumerate(ep_out_data_bits):
                if o_b is not None:
                    res.append(
                        If(endp._eq(i),
                           o_b(val),
                        )
                    )
            return res

        def set_ep_in_data_bit(val):
            res = []
            for i, i_b in enumerate(ep_in_data_bits):
                if i_b is not None:
                    res.append(
                        If(endp._eq(i),
                           i_b(val),
                        )
                    )
            return res

        return ep_out_data_bit, ep_in_data_bit, set_ep_out_data_bit, set_ep_in_data_bit, ep_is_isochronous

    def usb_endpoint_fsm(self, usb_rst: RtlSignal, chirp_en: RtlSignal,
               ep_rx: AxiStream,
               ep_tx: AxiStream,
               ep_tx_success: VldSynced,
               ep_rx_stall: RtlSignal,
               ep_tx_stall: RtlSignal,
               ):
        st_t = HEnum("usb_endpoint_fsm_st_t", [
            "RX_IDLE",
            "RX_DATA",
            "RX_DATA_IGNORE",
            "RX_DATA_IGNORE_NO_RESP",
            "TX_DATA",
            "TX_DATA_COMPLETE",
            "TX_HANDSHAKE",
            "TX_CHIRP",
        ])
        rst_any = self.rst_n._isOn() | (usb_rst._isOn() & ~chirp_en)
        st = self._reg("usb_endpoint_fsm_st", st_t, def_val=st_t.RX_IDLE, rst=rst_any)

        # tx drive
        token_pid = self.sie_rx.rx_header.pid
        rx_data = self.sie_rx.rx_data
        tx_cmd = self.sie_tx.tx_cmd

        ep_out_data_bit, ep_in_data_bit, set_ep_out_data_bit, set_ep_in_data_bit, ep_is_isochronous = self.define_endpoint_states(self.sie_rx.rx_header.endp, rst_any)

        out_pid_error = rename_signal(self, ~ep_is_isochronous & self.sie_rx.rx_header.vld & (
            (~ep_out_data_bit & (token_pid != USB_PID.DATA_0)) |
            (ep_out_data_bit & (token_pid != USB_PID.DATA_1))
        ), "out_pid_error")

        tx_cmd_extra_last = self._sig("tx_cmd_extra_last")
        tx_pid = self._reg("tx_pid", usb_pid_t)
        CodeBlock(
            tx_cmd.pid(None),
            tx_cmd.chirp(0),
            tx_cmd.valid(0),
            tx_cmd_extra_last(0),
            Switch(st)\
            .Case(st_t.RX_IDLE,
                tx_pid(None),
                If(self.sie_rx.rx_header.vld,
                    Switch(token_pid)\
                    .Case(USB_PID.TOKEN_IN,  # tx (device -> host)
                        If(ep_tx_stall,
                            # the endpoint is shut down or not supported
                            st(st_t.TX_HANDSHAKE),
                            tx_pid(USB_PID.HS_STALL),
                        ).Elif(ep_tx.valid,
                            # will send regular data
                            st(st_t.TX_DATA),
                             # [todo] MDATA for isochronous endpoints
                            If(ep_in_data_bit._eq(0),
                               tx_pid(USB_PID.DATA_0),
                            ).Else(
                               tx_pid(USB_PID.DATA_1),
                            ),
                        ).Else(
                            # no data to send
                            st(st_t.TX_HANDSHAKE),
                            tx_pid(USB_PID.HS_NACK),
                        )
                    ).Case(USB_PID.PING,  #  (device -> host, asking for host -> device)
                        st(st_t.TX_HANDSHAKE),
                        If(ep_rx_stall,
                            # the endpoint is shut down or not supported
                            tx_pid(USB_PID.HS_STALL),
                        ).Elif(ep_tx.valid,
                            tx_pid(USB_PID.HS_ACK),
                        ).Else(
                            # no data to send
                            tx_pid(USB_PID.HS_NACK),
                        ),
                    ).Case(USB_PID.TOKEN_OUT,  # rx (host -> device)
                        If(ep_rx_stall,
                           # the endpoint is shut down or not supported
                           tx_pid(USB_PID.HS_STALL),
                           st(st_t.RX_DATA_IGNORE),
                        ).Elif(ep_rx.ready,
                           st(st_t.RX_DATA),
                        ).Else(
                           # no space in rx buffer
                           tx_pid(USB_PID.HS_NACK),
                           st(st_t.RX_DATA_IGNORE),
                        )
                    ).Case(USB_PID.TOKEN_SETUP,  # (host -> device)
                        set_ep_out_data_bit(0),
                        set_ep_in_data_bit(1),
                        If(ep_rx.ready,
                           # can receive the setup data
                           st(st_t.RX_DATA),
                        ).Else(
                           # no space in rx buffer (note that this should not happen)
                           tx_pid(USB_PID.HS_NACK),
                           st(st_t.RX_DATA_IGNORE),
                        )
                    )
                ).Elif(chirp_en,
                    st(st_t.TX_CHIRP),
                ),
            ).Case(st_t.RX_DATA,
                # checking if data PID is correct
                # [TODO] isochronous rx
                # [TODO] timeout
                If(out_pid_error,
                    st(st_t.RX_DATA_IGNORE_NO_RESP),
                ).Elif(rx_data.error | (ep_is_isochronous & rx_data.vld & rx_data.last),
                    # no response on CRC error or isochronous enpoint
                    st(st_t.RX_IDLE),
                ).Elif(rx_data.vld & rx_data.last,
                    # ack after data receive
                    tx_pid(USB_PID.HS_ACK),
                    set_ep_out_data_bit(~ep_out_data_bit),
                    st(st_t.TX_HANDSHAKE)
                ),
            ).Case(st_t.RX_DATA_IGNORE_NO_RESP,
                If(rx_data.vld & rx_data.last,
                    st(st_t.RX_IDLE),
                )
            ).Case(st_t.RX_DATA_IGNORE,
                # there was an error, waiting until end of packet
                If(rx_data.vld & rx_data.last,
                    If(rx_data.error | ep_is_isochronous,
                        # no response on CRC error or isochronous enpoint
                        st(st_t.RX_IDLE),
                    ).Else(
                        st(st_t.TX_HANDSHAKE)
                    )
                )
            ).Case(st_t.TX_DATA,
                tx_cmd.pid(tx_pid),
                tx_cmd.valid(ep_tx.valid),
                If(ep_tx.valid & ep_tx.ready & ep_tx.last,
                   set_ep_in_data_bit(~ep_in_data_bit),
                   st(st_t.TX_DATA_COMPLETE),
                ),
            ).Case(st_t.TX_DATA_COMPLETE,
                st(st_t.RX_IDLE),
            ).Case(st_t.TX_HANDSHAKE,
                tx_cmd.valid(1),
                tx_cmd_extra_last(1),
                If(ep_tx_stall,
                    tx_cmd.pid(USB_PID.HS_STALL),
                ).Else(
                    tx_cmd.pid(tx_pid),
                ),
                If(tx_cmd.ready,
                    st(st_t.RX_IDLE),
                ),
            ).Case(st_t.TX_CHIRP,
                tx_cmd.valid(1),
                tx_cmd.pid(0),
                tx_cmd.chirp(1),
                If(~chirp_en,
                   st(st_t.RX_IDLE),
                )
            )
        )

        ep_rx.valid(rx_data.vld & st._eq(st_t.RX_DATA))
        ep_tx_success.vld(st._eq(st_t.TX_DATA_COMPLETE) & tx_cmd.ready)
        ep_tx_success.data(1)
        ep_tx.ready(((st._eq(st_t.TX_HANDSHAKE) & ep_tx_stall) |
                      st._eq(st_t.TX_DATA)
                      ) & tx_cmd.ready)
        return tx_cmd_extra_last

    def ms_to_clock_ticks(self, t_ms):
        return (t_ms * 1e-3) / (1 / self.CLK_FREQ)

    def usb_linerate_negotiation(self,
                                 enable: RtlSignalBase, usb_reset: RtlSignal,
                                 utmi: Utmi_8b, usb_speed_o:VldSynced):
        # Default - disconnect
        st_t = HEnum("usb_linerate_negotiation_state", [
            "IDLE",
            "WAIT_RST",
            "SEND_CHIRP_K",
            "WAIT_CHIRP_JK",
            "FULLSPEED",
            "HIGHSPEED",
        ])
        st = self._reg("usb_linerate_negotiation_state", st_t,
                       def_val={
                           None: st_t.IDLE,
                           USB_VER.USB1_1:st_t.FULLSPEED,
                           USB_VER.USB2_0:st_t.HIGHSPEED,
                       }[self.PRE_NEGOTIATED_TO])
        st_t = st._dtype
        utmi_fn = utmi.function_control
        utmi_otg = utmi.otg_control
        utmi_otg_default = utmi_otg._dtype.from_py({
            k: 0 if k in ("DpPulldown", "DmPulldown") else v
            for k, v in  ulpi_reg_otg_control_t_reset_defaults.items()
        })
        utmi_otg(utmi_otg_default)
        utmi_fn.Reset(ulpi_reg_function_control_t_reset_default["Reset"])
        utmi_fn.SuspendM(ulpi_reg_function_control_t_reset_default["SuspendM"])

        HS_CHIRP_COUNT = 5
        chirp_count_q = self._reg("chirp_count_q", uint8_t, def_val=0)
        last_LineState = self._reg("last_LineState", utmi.LineState._dtype, def_val=USB_LINE_STATE.SE0)
        last_LineState(utmi.LineState)

        If(st._eq(st_t.SEND_CHIRP_K),
            chirp_count_q(0),
        ).Elif(st._eq(st_t.WAIT_CHIRP_JK) & (last_LineState != utmi.LineState) & (chirp_count_q != 0xFF),
            chirp_count_q(chirp_count_q + 1)
        )

        ms = self.ms_to_clock_ticks
        DETACH_TIME = ms(1)  # 1ms -> T0
        ATTACH_FS_TIME = DETACH_TIME + ms(3)  # T0 + 3ms = T1
        CHIRPK_TIME = ATTACH_FS_TIME + ms(1)  # T1 + ~1ms
        HS_RESET_TIME = DETACH_TIME + ms(9)  # T0 + 10ms = T9
        # Time since T0 (start of HS reset)
        usb_rst_time_q = self._reg("usb_rst_time_q", Bits(log2ceil(HS_RESET_TIME)), def_val=0)

        If((st != st_t.WAIT_RST) & st.next._eq(st_t.WAIT_RST),
           # Entering wait for reset state
           usb_rst_time_q(0),
        ).Elif(st._eq(st_t.WAIT_RST) & (utmi.LineState != USB_LINE_STATE.SE0),
            # Waiting for reset, reset count on line state toggle
            usb_rst_time_q(0),
        ).Elif(usb_rst_time_q != mask(usb_rst_time_q._dtype.bit_length()),
            usb_rst_time_q(usb_rst_time_q + 1),
        )

        OP_MODE = Utmi_8b.OP_MODE
        XCVR_SELECT = Utmi_8b.XCVR_SELECT
        TERM_SELECT = Utmi_8b.TERM_SELECT

        def set_mode(OpMode: Utmi_8b.OP_MODE,
                     XcvrSelect: Utmi_8b.XCVR_SELECT,
                     TermSelect: Utmi_8b.TERM_SELECT):
            return [
                utmi_fn.OpMode(OpMode),
                utmi_fn.XcvrSelect(XcvrSelect),
                utmi_fn.TermSelect(TermSelect),
            ]

        Switch(st)\
        .Case(st_t.IDLE,
            set_mode(OP_MODE.NON_DRIVING, XCVR_SELECT.HS, TERM_SELECT.HS),
            # Detached
            If(enable & (usb_rst_time_q > DETACH_TIME),
                st(st_t.WAIT_RST),
            )
        ).Case(st_t.WAIT_RST,
            # Assert FS mode, check for SE0 (T0)
            set_mode(OP_MODE.NORMAL, XCVR_SELECT.FS, TERM_SELECT.FS),
            # Wait for SE0 (T1), send device chirp K
            If(usb_rst_time_q > ATTACH_FS_TIME,
                st(st_t.SEND_CHIRP_K),
            )
        ).Case(st_t.SEND_CHIRP_K,
            # Send chirp K
            set_mode(OP_MODE.DISABLE_BIT_STUFFING_AND_NRZI, XCVR_SELECT.HS, TERM_SELECT.FS),

            # End of device chirp K (T2)
            If(usb_rst_time_q > CHIRPK_TIME,
                st(st_t.WAIT_CHIRP_JK),
            )
        ).Case(st_t.WAIT_CHIRP_JK,
            # Stop sending chirp K and wait for downstream port chirps
            set_mode(OP_MODE.DISABLE_BIT_STUFFING_AND_NRZI, XCVR_SELECT.HS, TERM_SELECT.FS),
            # Required number of chirps detected, move to HS mode (T7)
            If(chirp_count_q > HS_CHIRP_COUNT,
                st(st_t.HIGHSPEED),
            # Time out waiting for chirps, fallback to FS mode
            ).Elif(usb_rst_time_q > HS_RESET_TIME,
                st(st_t.FULLSPEED),
            )
        ).Case(st_t.FULLSPEED,
            set_mode(OP_MODE.NORMAL, XCVR_SELECT.FS, TERM_SELECT.FS),
            # USB reset detected...
            If((usb_rst_time_q > HS_RESET_TIME) & usb_reset,
                st(st_t.WAIT_RST),
            ),
        ).Case(st_t.HIGHSPEED,
            # Enter HS mode
            set_mode(OP_MODE.NORMAL, XCVR_SELECT.HS, TERM_SELECT.HS),
            # Long SE0 - could be reset or suspend
            # TODO: Should revert to FS mode and check...
            If((usb_rst_time_q > HS_RESET_TIME) & usb_reset,
                st(st_t.WAIT_RST),
            )
        )
        Switch(st)\
        .Case(st_t.FULLSPEED,
            usb_speed_o.vld(1),
            usb_speed_o.data(USB_VER.values.index(USB_VER.USB1_1)),
        ).Case(st_t.HIGHSPEED,
            usb_speed_o.vld(1),
            usb_speed_o.data(USB_VER.values.index(USB_VER.USB2_0)),
        ).Default(
            usb_speed_o.vld(0),
            usb_speed_o.data(None),
        )

        chirp_en = st._eq(st_t.SEND_CHIRP_K)
        return chirp_en

    def _impl(self):
        phy = self.phy
        ep = self.ep
        sie_rx = self.sie_rx
        sie_tx = self.sie_tx

        usb_rst = self.detect_usb_rst(phy.LineState, self.usb_speed)
        chirp_en = self.usb_linerate_negotiation(BIT.from_py(1), usb_rst, phy, self.usb_speed)
        tx_cmd_extra_last = self.usb_endpoint_fsm(usb_rst, chirp_en, ep.rx, ep.tx, ep.tx_success, ep.rx_stall, ep.tx.valid & ep.tx_stall)

        endp = self._reg("endp", HStruct(
            (usb_endp_t, "data"),
            (BIT, "vld")
            ),
            def_val={"vld": 0}, rst=self.rst_n._isOn() | usb_rst
        )
        If(sie_rx.rx_header.vld,
           endp.data(sie_rx.rx_header.endp),
           endp.vld(~sie_rx.rx_header.error),
           ep.endp.data(sie_rx.rx_header.endp),
           ep.endp.vld(~sie_rx.rx_header.error),
        ).Else(
           ep.endp(endp)
        )

        # tx - device to host
        phy.tx(sie_tx.tx)
        sie_tx.tx_cmd.data(ep.tx.data)
        sie_tx.tx_cmd.keep(ep.tx.keep)
        sie_tx.tx_cmd.last(ep.tx.last | ep.tx_stall | tx_cmd_extra_last)
        sie_tx.enable(~usb_rst)

        # rx - host to device
        sie_rx.rx(phy.rx)
        ep.rx.data(sie_rx.rx_data.data)
        ep.rx.keep(sie_rx.rx_data.keep)
        ep.rx.last(sie_rx.rx_data.last)
        ep.rx.user(sie_rx.rx_data.error)

        sie_rx.current_usb_addr(self.current_usb_addr)
        sie_rx.enable(~usb_rst & ~chirp_en)
        self.usb_rst(usb_rst)

        propagateClkRstn(self)


def _example_Usb2DeviceCore():
    from hwtLib.peripheral.usb.descriptors.cdc import get_default_usb_cdc_vcp_descriptors
    u = Usb2DeviceCore()
    u.DESCRIPTORS = get_default_usb_cdc_vcp_descriptors()
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_Usb2DeviceCore()
    print(to_rtl_str(u))
