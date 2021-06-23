from hwt.interfaces.std import VldSynced, Signal
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from hwtLib.amba.axis import AxiStream
from hwtLib.peripheral.usb.constants import usb_endp_t
from hwtLib.peripheral.usb.descriptors.std import USB_ENDPOINT_ATTRIBUTES_TRANSFER_TYPE
from ipCorePackager.constants import DIRECTION


class UsbEndpointInterface(Interface):
    """
    An interface to transfer data between the USB core and endpont memory/usb function

    :attention: Transfers do have all potential data packets merged into
        a single one (both rx/tx, usb core or application needs to do splitting if required)
        this is to simplify checking and computing of data PID values
        and to handle all packet length limitations in usb core

    :ivar ep: endpoint number
    :ivar stall: 1 if endpoint is dissabled or request is not supported
    :ivar rx: data from host to device(function)
    :attention: if error(rx.user=1) appears during the transfer the frame has to be discardded in te endpoint buffer
        the error flag is latched until end of packet
    :ivar tx: data from device(function) to host
    :ivar tx_success: tells the endpoint buffer that previously send packet was successfully transfered
        and the packet can be deallocated (if tx_sucess.vld & ~tx_sucess.data it means that the packet needs to be retransmited)
    :note: for Isochronous endponts tx_sucess always returns success because isochronous transfers do not support
        retransmission

    .. hwt-autodoc::
    """
    USB_ENDPOINT_ATTRIBUTES_TRANSFER_TYPE

    def _config(self):
        self.HAS_RX = Param(True)
        self.HAS_TX = Param(True)
        self.DATA_WIDTH = Param(8)

    def _declr(self):
        self.endp = VldSynced()
        self.endp.DATA_WIDTH = usb_endp_t.bit_length()

        if self.HAS_RX:
            self.rx_stall = Signal(masterDir=DIRECTION.IN)
            rx = AxiStream()
            rx.DATA_WIDTH = self.DATA_WIDTH
            rx.USE_KEEP = True
            rx.USER_WIDTH = 1
            self.rx = rx

        if self.HAS_TX:
            self.tx_stall = Signal(masterDir=DIRECTION.IN)
            tx = self.tx = AxiStream(masterDir=DIRECTION.IN)
            tx.DATA_WIDTH = self.DATA_WIDTH
            tx.USE_KEEP = True

            self.tx_success = VldSynced()
            self.tx_success.DATA_WIDTH = 1
