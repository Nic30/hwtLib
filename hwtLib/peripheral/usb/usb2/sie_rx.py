#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import inf

from hwt.code import If, Concat
from hwt.code_utils import rename_signal
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.defs import BIT
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.std import Signal, Handshaked
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.builder import AxiSBuilder
from hwtLib.amba.axis_comp.frame_parser import AxiS_frameParser
from hwtLib.logic.crc import Crc
from hwtLib.logic.crcComb import CrcComb
from hwtLib.logic.crcPoly import CRC_5_USB, CRC_16_USB
from hwtLib.peripheral.usb.constants import usb_addr_t, usb_pid_t, usb_endp_t, \
    USB_PID, usb_crc5_t
from hwtLib.peripheral.usb.usb2.sie_interfaces import Usb2SieRxOut, \
    DataErrVldKeepLast
from hwtLib.peripheral.usb.usb2.utmi import Utmi_8b_rx


class Usb2SieDeviceRx(Unit):
    """
    UTMI rx (host->device) packet parser and CRC checker and cutter, (SIE stands for serial interface engine)

    :note: based on https://github.com/ultraembedded/core_usb_cdc
    """

    def _declr(self):
        addClkRstn(self)
        self.enable = Signal()
        self.rx = Utmi_8b_rx()
        self.current_usb_addr = Signal(usb_addr_t)

        self.rx_header: Usb2SieRxOut = Usb2SieRxOut()._m()
        self.rx_data: DataErrVldKeepLast = DataErrVldKeepLast()._m()
        self.rx_data.DATA_WIDTH = 8

    def _Utmi_8b_rx_to_DataErrVldStrbLast(self, rx: Utmi_8b_rx):
        rx_tmp = self._reg(
            "rx_tmp",
            HStruct(
                (rx.data._dtype, "data"),
                (BIT, "error"),
                (BIT, "valid"),
                (BIT, "active"),
            )[2],
            def_val=[
                {
                    "active": 0,
                    "valid": 0
                },
                {
                    "active": 0,
                    "valid": 0
                }
            ]
        )
        # we need to mark last valid data with last flag
        # If there was no data (and this is an error where even PID was not received sucessfuly)
        # we mark with the last the last invalid data before active went to 0

        rx_tmp[0].active(rx.active)
        If(rx.active,
            If(rx.valid,
                rx_tmp[0].data(rx.data),
                rx_tmp[0].valid(1),
                rx_tmp[0].error(rx.error),
            )
        ).Else(
            rx_tmp[0].data(None),
            rx_tmp[0].valid(0),
            rx_tmp[0].error(0),
        )

        rx_tmp[1](rx_tmp[0])
        rx_data_tmp = DataErrVldKeepLast()
        rx_data_tmp.DATA_WIDTH = rx.DATA_WIDTH
        rx_data_tmp.USE_KEEP = False

        self.rx_data_tmp = rx_data_tmp

        # :note: beat with keep=0 can apear only for zero lenght packet in the form of single workd with keep=0 last=1
        rx_data_tmp.data(rx_tmp[1].data)
        rx_data_tmp.error(rx_tmp[1].error)
        rx_data_tmp.last(~rx_tmp[0].active)
        # :note: delay of the last valid word so we can mark it with "last" flag
        rx_data_tmp.vld((rx_tmp[1].valid & rx_tmp[0].active & rx_tmp[0].valid) |
                        (rx_tmp[1].valid & rx_tmp[1].active & ~rx_tmp[0].active))

        return rx_data_tmp

    def _impl(self):
        rx = self._Utmi_8b_rx_to_DataErrVldStrbLast(self.rx)
        rx_ending = rename_signal(self, rx.vld & rx.last, "rx_ending")

        parser_pid = AxiS_frameParser(
            HStruct(
                (Bits(8), "pid"),
                (HStream(Bits(8), frame_len=(0, inf)), "data"),
            )
        )
        parser_token = AxiS_frameParser(
            HStruct(
                (usb_addr_t, "addr"),
                (usb_endp_t, "endp"),
                (usb_crc5_t, "crc5"),
            )
        )
        parser_payload = AxiS_frameParser(
            HStruct(
                (HStream(Bits(8), frame_len=[0, 1024]), "payload"),
                (Bits(16), "crc16"),
            )
        )
        for parser in [parser_pid, parser_token, parser_payload]:
            parser.DATA_WIDTH = 8
        parser_payload.USE_KEEP = True
        parser_token.OVERFLOW_SUPPORT = True

        self.parser_pid = parser_pid
        self.parser_token = parser_token
        self.parser_payload = parser_payload

        for parser in [parser_pid, parser_token, parser_payload]:
            # because input and output is just VldSynced and we can not stall the data
            for i in parser.dataOut._interfaces:
                if isinstance(i, Handshaked):
                    i.rd(1)
                elif isinstance(i, AxiStream):
                    pass
                else:
                    raise NotImplementedError(i)

        parser_pid.dataIn(rx, exclude=[parser_pid.dataIn.ready, parser_pid.dataIn.valid, rx.vld])
        parser_pid.dataIn.valid(rx.vld)

        after_pid = AxiSBuilder(self, parser_pid.dataOut.data)\
            .split_copy(2).end
        parser_token.dataIn(after_pid[0])
        parser_payload.dataIn(after_pid[1], exclude=[parser_payload.dataIn.keep])
        parser_payload.dataIn.keep(1)

        # restart or dissabld or end of the frame
        parse_fsm_rst_n = self.rst_n & ~self.enable & ~rx_ending

        token_q = self._reg("token_q", HStruct(
                (usb_pid_t, "pid"),
                (BIT, "pid_loaded"),
                (BIT, "err_pid"),
                (usb_addr_t, "addr"),
                (usb_endp_t, "endp"),
                (usb_crc5_t, "crc5"),
                (BIT, "crc5_loaded"),
                (BIT, "err_len"),
                (BIT, "valid"),  # mark that content of this register should be moved to output, it may contain some error set
            ),
            def_val={
                "pid_loaded": 0,
                "err_pid": 0,
                "crc5_loaded": 0,
                "err_len": 0,
                "valid": 0,
            }
        )
        pid = parser_pid.dataOut.pid

        # :attention: there are also SPLIT related PID values which are not supported
        pid_has_0b_data = rename_signal(
            self,
            pid.vld & USB_PID.is_hs(pid.data[4:]), "pid_has_0b_data")
        pid_has_16b_data = rename_signal(
            self,
            token_q.pid_loaded & (USB_PID.is_token(token_q.pid) | token_q.pid._eq(USB_PID.PING)),
            "pid_has_16b_data")
        pid_has_payload = rename_signal(
            self, token_q.pid_loaded & USB_PID.is_data(token_q.pid), "pid_has_payload")
        # packet with just pid contains something which should not
        err_packet_len_pid = rename_signal(
            self, pid_has_0b_data & ~rx_ending, "err_packet_len_pid")

        rx_data_ending = rename_signal(
            self,
            parser_pid.dataOut.data.valid & parser_pid.dataOut.data.last,
            "rx_data_ending")
        # token packet bytes missing or there are some extra
        err_packet_len_token = rename_signal(
            self,
            pid_has_16b_data & (rx_data_ending != parser_token.dataOut.crc5.vld),
            "err_packet_len_token")
        # the data packet is empty and missing also crc16 bytes
        err_packet_len_data = rename_signal(
            self,
            pid_has_payload & (rx_data_ending & (~parser_token.parsing_overflow & ~parser_token.dataOut.crc5.vld)),
            "err_packet_len_data")
        # [todo] 1 word out to mark 0 len packets
        If(self.enable & pid.vld,
           token_q.pid(pid.data[4:]),
           token_q.pid_loaded(1),
           token_q.err_pid((pid.data[4:] != ~pid.data[:4])),
           token_q.err_len(err_packet_len_pid),
           token_q.valid(pid_has_0b_data | err_packet_len_pid),
        ).Elif(self.enable & parser_token.dataOut.crc5.vld & ~token_q.err_len & ~token_q.err_pid,
           token_q.crc5_loaded(pid_has_16b_data),
           token_q.err_len(err_packet_len_token),
           token_q.valid(1),  # the data are sent using a different channel, we are sending header now
        ).Elif((token_q.valid & (token_q.err_len | err_packet_len_data | ~pid_has_payload))
               | (pid_has_payload & rx_ending)
               | (token_q.err_pid & rx_ending)
               | ~self.enable,
            token_q.pid(None),
            token_q.err_pid(0),
            token_q.pid_loaded(0),
            token_q.crc5_loaded(0),
            token_q.err_len(0),
            token_q.valid(0),
        ).Elif(token_q.valid & pid_has_payload,
            token_q.valid(0),
        )

        for token_field_name in ["addr", "endp", "crc5"]:
            p_intf = getattr(parser_token.dataOut, token_field_name)
            If(p_intf.vld & pid_has_16b_data,
               getattr(token_q, token_field_name)(p_intf.data)
            )

        # crc for token headers
        crc5 = CrcComb()
        crc5.DATA_WIDTH = usb_addr_t.bit_length() + usb_endp_t.bit_length()
        crc5.setConfig(CRC_5_USB)
        crc5.REFIN = False
        crc5.IN_IS_BIGENDIAN = True
        self.crc5 = crc5
        crc5.dataIn(Concat(token_q.endp, token_q.addr))

        err_addr = rename_signal(self, token_q.crc5_loaded & (self.current_usb_addr != token_q.addr), "err_addr")
        err_token_crc = rename_signal(self, token_q.crc5_loaded & (crc5.dataOut != token_q.crc5), "err_token_crc")

        rx_header = self.rx_header
        # valid for 1 clk period after word with crc5 or input rx data stream ended prematurely
        rx_header.vld(token_q.valid)
        rx_header.error(err_addr | err_token_crc | token_q.err_len)
        rx_header.pid(token_q.pid)
        rx_header.endp(token_q.endp)
        rx_header.frame_number(token_q.pid._eq(USB_PID.TOKEN_SOF)._ternary(Concat(token_q.endp, token_q.addr),
                                                                           rx_header.frame_number._dtype.from_py(None)))

        # crc for payload data
        crc16 = Crc()
        crc16.LATENCY = 0
        crc16.setConfig(CRC_16_USB)
        crc16.DATA_WIDTH = 8
        self.crc16 = crc16
        crc16.rst_n(parse_fsm_rst_n)
        payload = parser_payload.dataOut.payload
        crc16.dataIn.data(payload.data)
        crc16.dataIn.vld(payload.valid)
        payload.ready(1)

        # it would be better to use residue
        err_data_crc = rename_signal(
            self,
             pid_has_payload &
             parser_payload.dataOut.crc16.vld &
            (crc16.dataOut != parser_payload.dataOut.crc16.data), "err_data_crc")

        rx_data = self.rx_data
        rx_data.error(err_data_crc | token_q.err_len | (rx.vld & rx.error) | err_packet_len_data)
        is_0B_payload = rename_signal(self, pid_has_payload & rx_data_ending & parser_token.dataOut.crc5.vld, "is_0B_payload")
        If(is_0B_payload,
            rx_data.keep(0),
            rx_data.data(None),
        ).Else(
            rx_data.keep(payload.keep),
            rx_data.data(payload.data),
        )
        rx_data.vld(payload.valid | is_0B_payload | err_packet_len_data)
        rx_data.last(payload.last | is_0B_payload | err_packet_len_data)

        propagateClkRstn(self)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = Usb2SieDeviceRx()
    print(to_rtl_str(u))
