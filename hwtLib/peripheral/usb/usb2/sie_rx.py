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
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.logic.crc import Crc
from hwtLib.logic.crcComb import CrcComb
from hwtLib.logic.crcPoly import CRC_5_USB, CRC_16_USB
from hwtLib.peripheral.usb.constants import usb_addr_t, usb_pid_t, usb_endp_t, \
    USB_PID, usb_crc5_t
from hwtLib.peripheral.usb.usb2.sie_interfaces import Usb2SieRxOut, \
    DataErrVldKeepLast
from hwtLib.peripheral.usb.usb2.utmi import Utmi_8b_rx
from pyMathBitPrecise.bit_utils import mask


class Usb2SieDeviceRx(Unit):
    """
    UTMI rx (host->device) packet parser and CRC checker and cutter, (SIE stands for serial interface engine)

    :note: based on https://github.com/ultraembedded/core_usb_cdc


    .. hwt-autodoc::
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
            parser.UNDERFLOW_SUPPORT = True

        parser_pid.USE_KEEP = True
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

        parser_pid.dataIn(rx, exclude=[parser_pid.dataIn.ready, parser_pid.dataIn.valid, parser_pid.dataIn.keep, rx.vld])
        parser_pid.dataIn.valid(rx.vld)
        parser_pid.dataIn.keep(mask(parser_pid.dataIn.keep._dtype.bit_length()))

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
        pid: Handshaked = parser_pid.dataOut.pid

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

        after_pid: AxiStream = parser_pid.dataOut.data
        StreamNode(
            [after_pid],
            [parser_token.dataIn, parser_payload.dataIn],
            extraConds={
                parser_token.dataIn: pid_has_16b_data,
                parser_payload.dataIn: pid_has_payload,
            },
            skipWhen={
                parser_token.dataIn:~pid_has_16b_data,
                parser_payload.dataIn:~pid_has_payload,
            }
        ).sync()
        parser_token.dataIn(after_pid, exclude=[after_pid.ready, after_pid.valid])
        parser_payload.dataIn(after_pid, exclude=[after_pid.ready, after_pid.valid])

        # [todo] 1 word out to mark 0 len packets
        If(self.enable & pid.vld,
           token_q.pid(pid.data[4:]),
           token_q.pid_loaded(1),
           token_q.err_pid((pid.data[4:] != ~pid.data[:4])),
           token_q.err_len(err_packet_len_pid),
           token_q.valid(pid_has_0b_data | (pid.vld & USB_PID.is_data(pid.data[4:])) | err_packet_len_pid),
        ).Elif(self.enable & pid_has_16b_data & parser_token.dataOut.crc5.vld & ~token_q.err_len & ~token_q.err_pid,
           token_q.crc5_loaded(pid_has_16b_data),
           token_q.err_len(err_packet_len_token),
           token_q.valid(1),  # the data are sent using a different channel, we are sending header now
        ).Elif((token_q.valid & (token_q.err_len | ~pid_has_payload))
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
        crc5.REFOUT = False  # because the crc5 already commes reversed
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
        crc16.LATENCY = 1
        crc16.setConfig(CRC_16_USB)
        crc16.DATA_WIDTH = 8
        self.crc16 = crc16
        # restart or dissabled or end of the frame
        payload: AxiStream = parser_payload.dataOut.payload
        crc16.dataIn.data(payload.data)
        crc16.dataIn.vld(payload.valid & payload.keep)
        # buffer to assert that the crc error flag is set in last word
        payload = AxiSBuilder(self, payload).buff(2).end
        payload_end = payload.ready & payload.valid & payload.last
        crc16.rst_n(self.rst_n & self.enable & ~payload_end)
        payload.ready(1)

        # it would be better to use residue
        err_data_crc16 = rename_signal(
            self,
             parser_payload.dataOut.crc16.vld &
            (Concat(*(b for b in crc16.dataOut)) != parser_payload.dataOut.crc16.data), "err_data_crc")

        rx_data = self.rx_data

        err_data_crc16_delayed = self._reg("err_data_crc16_delayed", BIT[2], def_val=[0, 0])
        # for the case where packet len < min size
        err_data_crc16_delayed[0](err_data_crc16 | parser_payload.error_underflow)
        err_data_crc16_delayed[1](err_data_crc16_delayed[0] | parser_payload.error_underflow)
        rx_data.error(err_data_crc16 |
                      err_data_crc16_delayed[0] |
                      err_data_crc16_delayed[1] |
                      (rx.vld & rx.error))  # [todo] this rx error can be of next frame instead of this one
        rx_data.keep(payload.keep)
        If(~payload.keep | rx_data.error,
           rx_data.data(None)
        ).Else(
           rx_data.data(payload.data)
        )
        rx_data.vld(payload.valid)
        rx_data.last(payload.last | rx_data.error)

        propagateClkRstn(self)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = Usb2SieDeviceRx()
    print(to_rtl_str(u))
