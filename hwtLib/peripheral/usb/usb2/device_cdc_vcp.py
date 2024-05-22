#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Switch
from hwt.code_utils import rename_signal
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.hwIOStruct import HwIOStruct
from hwt.hwIOs.std import HwIODataRdVld
from hwt.hwIOs.utils import propagateClkRstn
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.peripheral.usb.descriptors.bundle import UsbDescriptorBundle, \
    UsbEndpointMeta
from hwtLib.peripheral.usb.descriptors.cdc import get_default_usb_cdc_vcp_descriptors, \
    CLASS_REQUEST, make_usb_line_coding_default
from hwtLib.peripheral.usb.usb2.device_common import Usb2DeviceCommon
from hwtLib.peripheral.usb.usb2.device_ep_buffers import UsbDeviceEpBuffers
from hwtLib.types.ctypes import uint8_t


class Usb2CdcVcp(Usb2DeviceCommon):
    """
    USB2.0 communication device class virtual com port core (serial/uart over USB)

    :see: :class:`hwtLib.peripheral.usb.usb2.device_common.Usb2DeviceCommon`
    :ivar RX_AGGREGATION_TIMEOUT: the timeout (in clk ticks) for a packing of incomming bytes
        to a USB packet (the bigger packet equals more USB efficiency)
    :ivar rx: stream data from host
    :ivar tx: stream data to host

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        Usb2DeviceCommon.hwConfig(self)
        self.DESCRIPTORS: UsbDescriptorBundle = get_default_usb_cdc_vcp_descriptors(
            productStr=self.__class__.__name__,
            bMaxPacketSize=512)
        self.RX_AGGREGATION_TIMEOUT = HwParam(512)

    @override
    def hwDeclr(self):
        Usb2DeviceCommon.hwDeclr(self)
        self.rx:HwIODataRdVld = HwIODataRdVld()._m()
        self.tx = HwIODataRdVld()
        for i in [self.rx, self.tx]:
            i.DATA_WIDTH = 8

    def generat_descriptor_rom(self, descriptors: UsbDescriptorBundle, rst):
        _descriptor_rom = descriptors.compile_rom()
        line_coding = descriptors.HConst_to_byte_list(make_usb_line_coding_default())
        descriptors.ROM_CDC_LINE_CODING_ADDR = len(descriptors)
        descriptors.ROM_CDC_LINE_CODING_SIZE = len(line_coding)
        _descriptor_rom.extend(line_coding)
        descriptor_rom = self._sig("descriptor_rom", HBits(8)[len(_descriptor_rom)], def_val=_descriptor_rom)
        # a register for descriptor reader
        descr_addr = self._reg("descr_addr", uint8_t, rst=rst)
        descr_d = descriptor_rom[descr_addr]
        return descr_addr, descr_d

    def decode_setup_request_class(self, setup:HwIOStruct, ep0_stall: RtlSignal, usb_addr_next: RtlSignal,
                            descriptors: UsbDescriptorBundle,
                            req_bDescriptorType: RtlSignal, req_bDescriptorIndex: RtlSignal, dev_configured: RtlSignal,
                            descr_addr: RtlSignal, ep0_trans_len: RtlSignal):
        bRequest = rename_signal(self, setup.bRequest, "bRequest")
        return Switch(bRequest)\
                .Case(CLASS_REQUEST.GET_LINE_CODING,
                    descr_addr(descriptors.ROM_CDC_LINE_CODING_ADDR),
                    ep0_trans_len(descriptors.ROM_CDC_LINE_CODING_SIZE),
                )
                # accept all, from some reason there is bRequest 0x25 which should be reserved value when used with usbip

    @override
    def hwImpl(self):
        ep_meta = self.DESCRIPTORS.get_endpoint_meta()
        ep_meta = list(ep_meta)
        for ep0_channel in ep_meta[0]:
            ep0_channel: UsbEndpointMeta
            # no need to buffer anything as we can process it directly
            ep0_channel.buffer_size = 0

        # because we do not support any interrupts
        # the buffer will respond with the stall automatically
        for ep2_channel in ep_meta[2]:
            if ep2_channel is None:
                continue
            ep2_channel: UsbEndpointMeta
            # no need to buffer interrupts as we can process it directly
            ep2_channel.buffer_size = 0

        ep_buffers = UsbDeviceEpBuffers()
        ep_buffers.ENDPOINT_META = tuple(ep_meta)
        self.ep_buffers = ep_buffers

        dev_configured, ep0_stall = self.descriptor_ep0_fsm(self.DESCRIPTORS)
        self.connect_core_and_ep_buffers_common(ep0_stall, ep_buffers)

        tx_src = HsBuilder(self, self.tx).to_axis(
            MAX_FRAME_WORDS=ep_meta[1][0].max_packet_size,
            IN_TIMEOUT=self.RX_AGGREGATION_TIMEOUT).end

        ep_buffers.ep[1].tx(tx_src, exclude=[tx_src.ready, tx_src.valid, ep_buffers.ep[1].tx.keep])
        ep_buffers.ep[1].tx.keep(1)
        StreamNode([tx_src], [ep_buffers.ep[1].tx]).sync(dev_configured._eq(1))

        ep_buffers.ep[2].tx.data(None)
        ep_buffers.ep[2].tx.last(None)
        ep_buffers.ep[2].tx.keep(None)
        ep_buffers.ep[2].tx.valid(0)

        rx = ep_buffers.ep[1].rx
        StreamNode([rx], [self.rx]).sync(dev_configured._eq(1))
        self.rx.data(rx.data)

        propagateClkRstn(self)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    
    m = Usb2CdcVcp()
    print(to_rtl_str(m))
