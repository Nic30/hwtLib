#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Concat, If
from hwt.code_utils import rename_signal
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct
from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.frame_deparser import AxiS_frameDeparser
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.logic.crc import Crc
from hwtLib.logic.crcPoly import CRC_16_USB
from hwtLib.peripheral.usb.constants import usb_pid_t, USB_PID
from hwtLib.peripheral.usb.usb2.utmi import Utmi_8b_tx
from ipCorePackager.intfIpMeta import IntfIpMetaNotSpecified
from hwtLib.amba.axis_comp.builder import AxiSBuilder


class Usb2SieDeviceTxInput(AxiStream):
    """
    :attention: The valid must not go low in the middle of the packet

    .. hwt-autodoc::
    """

    def _config(self):
        AxiStream._config(self)
        self.USE_KEEP = True
        self.DATA_WIDTH = 8

    def _declr(self):
        self.pid = Signal(usb_pid_t)
        self.chirp = Signal()
        AxiStream._declr(self)

    def _getIpCoreIntfClass(self):
        raise IntfIpMetaNotSpecified()


class Usb2SieDeviceTx(Unit):
    """
    UTMI Tx packet CRC appender and chirp inserter, (SIE stands for serial interface engine)

    :attention: the zero lenght data packet has to have only a single word with keep=0 and last=1
    :note: supports handshake and data packets only
    :note: during chirp the continuous sequence of 0 is send over the channel
        until chirp signal is deasserted
    :see: :class:`~.UsbSieDeviceTxInput`

    :ivar tx_cmd: An interface which should be used to control this component
    :ivar tx: The Tx part of the Utmi_8b interface

    .. hwt-autodoc::
    """

    def _declr(self):
        addClkRstn(self)
        self.enable = Signal()

        self.tx_cmd = Usb2SieDeviceTxInput()

        self.tx = Utmi_8b_tx()._m()

    def _AxiStream_to_Utmi_8b_tx(self, axis: AxiStream, tx: Utmi_8b_tx):
        """
        Convert last signal to a space between packets
        """
        last_delayed = self._reg("_AxiStream_to_Utmi_8b_tx_last_delayed", def_val=0)
        StreamNode([axis], [tx]).sync(~last_delayed)
        If(last_delayed & tx.rd,
            last_delayed(0),
        ).Elif(axis.valid & axis.last & tx.rd,
            last_delayed(1),
        )
        tx.data(axis.data)

    def _impl(self):
        deparser_hs = AxiS_frameDeparser(
            HStruct(
                (Bits(8), "pid"),
            )
        )
        deparser_data = AxiS_frameDeparser(
            HStruct(
                (Bits(8), "pid"),
                (HStream(Bits(8), frame_len=(0, 1024)), "data"),
                (Bits(16), "crc16"),
            )
        )
        for d in [deparser_hs, deparser_data]:
            d.DATA_WIDTH = self.tx_cmd.DATA_WIDTH
            d.USE_STRB = False
            d.USE_KEEP = True

        self.deparser_hs = deparser_hs
        self.deparser_data = deparser_data

        tx_cmd: Usb2SieDeviceTxInput = AxiSBuilder(self, self.tx_cmd).buff(items=1).end
        pid_is_hs = rename_signal(self, tx_cmd.valid & ~tx_cmd.chirp & USB_PID.is_hs(tx_cmd.pid), "pid_is_hs")
        pid_has_data = rename_signal(self, tx_cmd.valid & ~tx_cmd.chirp & USB_PID.is_data(tx_cmd.pid), "pid_has_data")
        # pid_has_data_non_zero_len = rename_signal(self, pid_has_data & (tx_cmd.keep != 0), "pid_has_data_non_zero_len")
        pid_has_data_zero_len = rename_signal(self, pid_has_data & tx_cmd.keep._eq(0) & tx_cmd.last, "pid_has_data_zero_len")

        for d in [deparser_hs, deparser_data]:
            d.dataIn.pid.data(Concat(~tx_cmd.pid, tx_cmd.pid))

        is_sof_of_command = self._reg("is_sof_of_command", def_val=1)
        If(~self.enable | (tx_cmd.ready & tx_cmd.valid & tx_cmd.last),
           is_sof_of_command(1)
        ).Elif(tx_cmd.ready & tx_cmd.valid & ~tx_cmd.last,
           is_sof_of_command(0),
        )

        crc16_valid = self._reg("crc16_valid", def_val=0)
        # select a frame depending on type of pacekt defined by PID and presence of tx data
        StreamNode(
            [],
            [deparser_hs.dataIn.pid, deparser_data.dataIn.pid],
            extraConds={
                deparser_hs.dataIn.pid:pid_is_hs,
                deparser_data.dataIn.pid: pid_has_data,
            },
            skipWhen={
                deparser_hs.dataIn.pid: pid_has_data,
                deparser_data.dataIn.pid: pid_is_hs,
            }
        ).sync(tx_cmd.valid & self.enable & is_sof_of_command & ~crc16_valid)

        payload_in: AxiStream = deparser_data.dataIn.data
        StreamNode(
            [], [payload_in],
        ).sync(pid_has_data & tx_cmd.valid & ~crc16_valid)

        # tx_cmd consume
        StreamNode(
            [tx_cmd], [],
        ).sync(~crc16_valid & (
                        pid_is_hs & deparser_hs.dataIn.pid.rd |
                        (pid_has_data & payload_in.ready)
                    ))
        payload_in.data(tx_cmd.data)
        payload_in.last(tx_cmd.last)
        payload_in.keep(tx_cmd.keep)

        crc16 = Crc()
        crc16.LATENCY = 1
        crc16.setConfig(CRC_16_USB)
        crc16.DATA_WIDTH = tx_cmd.DATA_WIDTH
        self.crc16 = crc16

        crc16.rst_n(self.rst_n & ~(deparser_data.dataIn.crc16.vld & deparser_data.dataIn.crc16.rd))
        crc16.dataIn.data(payload_in.data)
        crc16.dataIn.vld(payload_in.valid & payload_in.ready & (payload_in.keep != 0))

        end_of_payload = rename_signal(self, payload_in.valid & payload_in.ready & payload_in.last, "end_of_payload")
        If(~crc16_valid & pid_has_data & end_of_payload,
           crc16_valid(1),
        ).Elif(deparser_data.dataIn.crc16.rd,
           crc16_valid(0)
        )
        # [TODO] check if reflection is done twice or not
        deparser_data.dataIn.crc16.data(Concat(*(b for b in crc16.dataOut)))
        deparser_data.dataIn.crc16.vld(crc16_valid | pid_has_data_zero_len)

        axis_tx = AxiStream()
        axis_tx.DATA_WIDTH = tx_cmd.DATA_WIDTH
        self.axis_tx = axis_tx
        _axis_tx = AxiSBuilder.join_prioritized(self, [deparser_hs.dataOut, deparser_data.dataOut]).end
        If(tx_cmd.valid & tx_cmd.chirp,
           axis_tx.data(0),
           axis_tx.last(0),
           axis_tx.valid(1),
           _axis_tx.ready(0),
        ).Else(
           axis_tx(_axis_tx, exclude=[_axis_tx.keep, ])
        )

        self._AxiStream_to_Utmi_8b_tx(axis_tx, self.tx)

        propagateClkRstn(self)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = Usb2SieDeviceTx()
    print(to_rtl_str(u))
