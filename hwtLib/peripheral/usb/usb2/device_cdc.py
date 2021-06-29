from typing import Optional

from hwt.code import Switch, If, In
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.enum import HEnum
from hwt.interfaces.std import Signal, Handshaked
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axis import AxiStream
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.peripheral.usb.constants import usb_addr_t
from hwtLib.peripheral.usb.descriptors.bundle import UsbDescriptorBundle, \
    UsbEndpointMeta
from hwtLib.peripheral.usb.descriptors.cdc import get_default_usb_cdc_vcp_descriptors, \
    CLASS_REQUEST, make_usb_line_coding_default
from hwtLib.peripheral.usb.descriptors.std import USB_DESCRIPTOR_TYPE, \
    usb_descriptor_configuration_t
from hwtLib.peripheral.usb.device_request import USB_REQUEST_TYPE_TYPE, \
    USB_REQUEST, usb_device_request_t, USB_REQUEST_TYPE_DIRECTION
from hwtLib.peripheral.usb.usb2.device_core import Usb2DeviceCore
from hwtLib.peripheral.usb.usb2.device_ep_buffers import UsbDeviceEpBuffers
from hwtLib.peripheral.usb.usb2.utmi import Utmi_8b
from hwtLib.types.ctypes import uint16_t, uint8_t


class Usb2Cdc(Unit):
    """
    USB2.0 communcation device class core (serial/uart over USB)

    :note: this component directly handles the functionality of the EP0 and connects the usb_core
        to ep_buffers, The
    :ivar usb_core: Handles the USB protocol reset, ping, SOF and handshake messages
    :ivar ep_buffers: handles the data multiplexing and replaying on errors,

    :ivar RX_AGGREGATION_TIMEOUT: the timeout (in clk ticks) for a packing of incomming bytes
        to a USB packet (the bigger packet equals more USB efficiency)
    :ivar rx: stream data from host
    :ivar tx: stream data to host

    .. hwt-autodoc::
    """

    def _config(self):
        Usb2DeviceCore._config(self)
        self.DESCRIPTORS: UsbDescriptorBundle = get_default_usb_cdc_vcp_descriptors(
            productStr=self.__class__.__name__,
            bMaxPacketSize=512)
        self.RX_AGGREGATION_TIMEOUT = Param(512)

    def _declr(self):
        addClkRstn(self)
        self.phy = Utmi_8b()
        self.usb_rst: Signal = Signal()._m()

        self.rx:Handshaked = Handshaked()._m()
        self.tx = Handshaked()
        for i in [self.rx, self.tx]:
            i.DATA_WIDTH = 8

        with self._paramsShared():
            self.usb_core = Usb2DeviceCore()

    def descriptor_ep0_fsm_get_descriptor(self, descr_bundle: UsbDescriptorBundle, setup_wLength: RtlSignal,
                                          req_bDescriptorType:RtlSignal, req_bDescriptorIndex:RtlSignal,
                                          descr_addr: RtlSignal, ep0_get_len: RtlSignal,
                                          ep0_stall: RtlSignal):
        """
        Get descriptor part of the FSM for EP0 configuration endpoint

        :param req_bDescriptorType: the bDescriptorType from the usb device request
        :param req_bDescriptorIndex: the bDescriptorIndex from the usb device request
        :param descr_addr: read address for current descriptor read
        :param ep0_get_len: size how many descriptor bytes should be read
        """

        def hmin(a, b):
            return (a < b)._ternary(a, b)

        def set_addr_len(_descr_addr:Optional[int], descr_len:Optional[int]):
            return [
                descr_addr(_descr_addr),
                ep0_get_len(None if descr_len is None else hmin(setup_wLength, descr_len)),
            ]

        get_descrs = descr_bundle.get_descriptors_from_rom
        return \
        Switch(req_bDescriptorType)\
        .Case(USB_DESCRIPTOR_TYPE.DEVICE,
              set_addr_len(*get_descrs(USB_DESCRIPTOR_TYPE.DEVICE)[0]),
        ).Case(USB_DESCRIPTOR_TYPE.CONFIGURATION,
            set_addr_len(
                get_descrs(USB_DESCRIPTOR_TYPE.CONFIGURATION)[0][0],
                int(descr_bundle.get_descriptor(usb_descriptor_configuration_t, 0)[1].body.wTotalLength)),
        ).Case(USB_DESCRIPTOR_TYPE.STRING,
            Switch(req_bDescriptorIndex).add_cases([
                (i, [descr_addr(addr), ep0_get_len(size)])
                for i, (addr, size) in enumerate(get_descrs(USB_DESCRIPTOR_TYPE.STRING))
            ]).Default(
                ep0_stall(1),
                set_addr_len(None, None)
            )
        ).Default(
            ep0_stall(1),
            set_addr_len(None, None)
        )

    def load_usb_device_request(self, rx:AxiStream, rst:RtlSignal):
        """
        :param rx: the port with incomming data
        :param rst: the usb reset or core reset
        """
        setup_byte_cnt = usb_device_request_t.bit_length() // 8
        setup_raw = self._reg("setup", Bits(usb_device_request_t.bit_length()))
        setup_rx_byte_i = self._reg("setup_rx_byte_i", Bits(log2ceil(setup_byte_cnt - 1)), def_val=0, rst=rst)

        def index_setup_byte(i: int):
            return setup_raw[(i + 1) * 8: i * 8]

        # loading of setup_raw register from setup data comming from the host
        If(rx.valid,
            If(rx.last,
               setup_rx_byte_i(0),
            ).Else(
               setup_rx_byte_i(setup_rx_byte_i + 1),
            ),
            Switch(setup_rx_byte_i).add_cases([
                 (i, index_setup_byte(i)(rx.data)) for i in range(setup_byte_cnt)
            ]),
        )
        # decoding of setup data
        setup = setup_raw._reinterpret_cast(usb_device_request_t)
        req_bDescriptorType, req_bDescriptorIndex = index_setup_byte(3), index_setup_byte(2),
        return setup, req_bDescriptorType, req_bDescriptorIndex

    def generat_descriptor_rom(self, descriptors: UsbDescriptorBundle, rst):
        _descriptor_rom = descriptors.compile_rom()
        line_coding = descriptors.HValue_to_byte_list(make_usb_line_coding_default())
        ROM_CDC_LINE_CODING_ADDR = len(descriptors)
        ROM_CDC_LINE_CODING_SIZE = len(line_coding)
        _descriptor_rom.extend(line_coding)
        descriptor_rom = self._sig("descriptor_rom", Bits(8)[len(_descriptor_rom)], def_val=_descriptor_rom)
        # a register for descriptor reader
        descr_addr = self._reg("descr_addr", uint8_t, rst=rst)
        descr_d = descriptor_rom[descr_addr]
        return (ROM_CDC_LINE_CODING_ADDR, ROM_CDC_LINE_CODING_SIZE), descr_addr, descr_d

    def decode_setup_request(self, setup:StructIntf, ep0_stall: RtlSignal, usb_addr_next: RtlSignal,
                            descriptors: UsbDescriptorBundle,
                            req_bDescriptorType: RtlSignal, req_bDescriptorIndex: RtlSignal, dev_configured: RtlSignal,
                            descr_addr: RtlSignal, ep0_trans_len: RtlSignal,
                            ROM_CDC_LINE_CODING_ADDR:int, ROM_CDC_LINE_CODING_SIZE:int):
        return \
            Switch(setup.bmRequestType.type)\
            .Case(USB_REQUEST_TYPE_TYPE.STANDARD,
                ep0_stall(0),
                Switch(setup.bRequest)\
                 .Case(USB_REQUEST.GET_STATUS,
                ).Case(USB_REQUEST.CLEAR_FEATURE,
                ).Case(USB_REQUEST.SET_FEATURE,
                ).Case(USB_REQUEST.SET_ADDRESS,
                    usb_addr_next(setup.wValue[7:0]),
                ).Case(USB_REQUEST.GET_DESCRIPTOR,
                    self.descriptor_ep0_fsm_get_descriptor(
                        descriptors,
                        setup.wLength,
                        req_bDescriptorType, req_bDescriptorIndex,
                        descr_addr, ep0_trans_len,
                        ep0_stall),
                ).Case(USB_REQUEST.GET_CONFIGURATION,
                ).Case(USB_REQUEST.SET_CONFIGURATION,
                    If(setup.wValue._eq(0),
                        dev_configured(0),
                    ).Elif(setup.wValue._eq(1),
                        dev_configured(1),
                    ).Else(
                        ep0_stall(1),
                    )
                ).Case(USB_REQUEST.GET_INTERFACE,
                    ep0_stall(1),
                ).Case(USB_REQUEST.SET_INTERFACE,
                    ep0_stall((setup.wValue != 0) | (setup.wIndex != 0)),
                ).Default(
                    ep0_stall(1),
                )
            ).Case(USB_REQUEST_TYPE_TYPE.VENDOR,
                # None supported
                ep0_stall(1),
            ).Case(USB_REQUEST_TYPE_TYPE.CLASS,
                Switch(setup.bRequest)\
                .Case(CLASS_REQUEST.GET_LINE_CODING,
                    descr_addr(ROM_CDC_LINE_CODING_ADDR),
                    ep0_trans_len(ROM_CDC_LINE_CODING_SIZE),
                )
            ).Default(
                ep0_stall(1)
            )

    def connect_ep0_data(self, ep0, setup_stage, descr_d, ep0_trans_len, actual_packet_split):
        setup_stage_t = setup_stage._dtype
        If(setup_stage._eq(setup_stage_t.DATA_GET),
           ep0.tx.data(descr_d),
           ep0.tx.keep(ep0_trans_len != 0),
           ep0.tx.last((ep0_trans_len < 2) | actual_packet_split),
        ).Else(
           ep0.tx.data(None),
           ep0.tx.keep(0),
           ep0.tx.last(1),
        )
        ep0.tx.valid(In(setup_stage, [setup_stage_t.DATA_GET, setup_stage_t.STATUS_IN]))
        ep0.rx.ready(In(setup_stage, [setup_stage_t.IDLE, setup_stage_t.STATUS_OUT, setup_stage_t.DATA_SET]))

    def descriptor_ep0_fsm(self, descriptors: UsbDescriptorBundle):
        """
        The Control enpoint (EP0) functionality
        """
        rst = self.rst_n._isOn() | self.usb_core.usb_rst._isOn()
        # address on usb bus
        usb_addr = self._reg("usb_addr", usb_addr_t, def_val=0, rst=rst)
        # a register with new usb_address which will be set in status stage
        usb_addr_next = self._reg("usb_addr_next", usb_addr_t, rst=rst)

        self.usb_core.current_usb_addr(usb_addr)

        # stall marks that the request is not supported
        ep0_stall = self._reg("ep0_stall", def_val=0, rst=rst)

        # marks that the device configuration was set using setup transaction and the device
        # configuration is finished
        dev_configured = self._reg("dev_configured", def_val=0, rst=rst)

        ep0 = self.ep_buffers.ep[0]
        setup, req_bDescriptorType, req_bDescriptorIndex = \
            self.load_usb_device_request(ep0.rx, rst)

        (ROM_CDC_LINE_CODING_ADDR, ROM_CDC_LINE_CODING_SIZE), \
            descr_addr, descr_d, = self.generat_descriptor_rom(descriptors, rst)
        ep0_trans_len = self._reg("ep0_trans_len", uint16_t, def_val=0, rst=rst)

        setup_stage_t = HEnum("setup_stage_t", ['IDLE', 'SETUP',
                                                'DATA_GET', 'DATA_SET',
                                                'STATUS_OUT', 'STATUS_IN'])
        setup_stage = self._reg("setup_stage", setup_stage_t, def_val=setup_stage_t.IDLE, rst=rst)
        EP0_MAX_TX_PACKET_SIZE = self.ep_buffers.ENDPOINT_META[0][0].max_packet_size
        packet_split_cntr = self._reg("packet_split_cntr", Bits(log2ceil(EP0_MAX_TX_PACKET_SIZE - 1)),
                                      def_val=0, rst=rst)

        # is_setup_get = setup_valid_q & setup.bmRequestType.data_transfer_direction._eq(USB_REQUEST_TYPE_DIRECTION.DEV_TO_HOST)
        is_setup_set = setup.bmRequestType.data_transfer_direction._eq(USB_REQUEST_TYPE_DIRECTION.HOST_TO_DEV)

        ep0 = self.ep_buffers.ep[0]

        Switch(setup_stage)\
        .Case(setup_stage_t.IDLE,
            If(ep0.rx.valid & ep0.rx.last,
               setup_stage(setup_stage_t.SETUP),
            ),
        ).Case(setup_stage_t.SETUP,
            # process setup request and decide what to send or receive next
            If(is_setup_set,
                If(setup.wLength._eq(0),
                   # ommit the datastage if there is no data
                   setup_stage(setup_stage_t.STATUS_IN),
                ).Else(
                   setup_stage(setup_stage_t.DATA_SET),
                ),
            ).Else(
                If(setup.wLength._eq(0),
                   setup_stage(setup_stage_t.STATUS_OUT),
                ).Else(
                   setup_stage(setup_stage_t.DATA_GET),
                ),
            ),
            # parse setup request and store importatnt values
            usb_addr_next(usb_addr),
            self.decode_setup_request(setup, ep0_stall, usb_addr_next, descriptors,
                                     req_bDescriptorType, req_bDescriptorIndex, dev_configured,
                                     descr_addr, ep0_trans_len,
                                     ROM_CDC_LINE_CODING_ADDR, ROM_CDC_LINE_CODING_SIZE),
            packet_split_cntr(0),
        ).Case(setup_stage_t.DATA_GET,
            # transmit as many packets as the ep0_get_len requres
            If(ep0.tx.ready,
                If(ep0_stall,
                   setup_stage(setup_stage_t.IDLE),
                   ep0_stall(0),
                ).Elif((ep0_trans_len < 2) & ((packet_split_cntr != EP0_MAX_TX_PACKET_SIZE - 1) & ep0_trans_len._eq(1)),
                   setup_stage(setup_stage_t.STATUS_OUT),
                ).Else(
                    descr_addr(descr_addr + 1),
                    packet_split_cntr(packet_split_cntr + 1),
                    ep0_trans_len(ep0_trans_len - 1),
                )
            )
        ).Case(setup_stage_t.DATA_SET,
            # receive as many packets as the ep0_get_len requires
            If(ep0.rx.valid,
                # [todo] if size % max_packet size == 0 the zero length packet at end is required
                If(ep0_stall,
                   setup_stage(setup_stage_t.IDLE),
                   ep0_stall(0),
                ).Elif(ep0_trans_len._eq(1) | ep0_trans_len._eq(0),
                   setup_stage(setup_stage_t.STATUS_IN),
                ),
                ep0_trans_len(ep0_trans_len - 1)
            )
        ).Case(setup_stage_t.STATUS_OUT,
            # receive 1 zero len packet
            If(ep0.rx.valid & ep0.rx.last,
                setup_stage(setup_stage_t.IDLE),
            )
        ).Case(setup_stage_t.STATUS_IN,
            # transmit 1 zero len packet
            If(ep0.tx.ready,
                setup_stage(setup_stage_t.IDLE),
                usb_addr(usb_addr_next),  # should only modify on SET_ADDRESS detected in decode_setup_request
            ),
        )
        # marks that the curent packet has to be splited on this word due to max packet size limitation
        actual_packet_split = packet_split_cntr._eq(EP0_MAX_TX_PACKET_SIZE - 1)
        self.connect_ep0_data(ep0, setup_stage, descr_d, ep0_trans_len, actual_packet_split)
        return dev_configured, ep0_stall

    def _impl(self):
        self.usb_core.phy(self.phy)
        self.usb_rst(self.usb_core.usb_rst)

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

        tx_src = HsBuilder(self, self.tx).to_axis(
            MAX_FRAME_WORDS=ep_meta[1][0].max_packet_size,
            IN_TIMEOUT=self.RX_AGGREGATION_TIMEOUT).end

        ep_buffers.usb_core_io.endp(self.usb_core.ep.endp)
        ep_buffers.usb_core_io.rx(self.usb_core.ep.rx)
        self.usb_core.ep.rx_stall(ep_buffers.usb_core_io.rx_stall)

        self.usb_core.ep.tx(ep_buffers.usb_core_io.tx)
        self.usb_core.ep.tx_stall(ep0_stall | ep_buffers.usb_core_io.tx_stall)
        # [todo] propagate errors from usb tx
        ep_buffers.usb_core_io.tx_success.vld(1)
        ep_buffers.usb_core_io.tx_success.data(1)

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
    from hwt.synthesizer.utils import to_rtl_str
    u = Usb2Cdc()
    print(to_rtl_str(u))
