from typing import Tuple, Optional, List

from hwt.code import Or, Switch, In
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.hObjList import HObjList
from hwt.synthesizer.param import Param
from hwt.synthesizer.unit import Unit
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.fifoCopy import AxiSFifoCopy
from hwtLib.amba.axis_comp.fifoDrop import AxiSFifoDrop
from hwtLib.amba.axis_fullduplex import AxiStreamFullDuplex
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.peripheral.usb.descriptors.bundle import UsbEndpointMeta
from hwtLib.peripheral.usb.usb2.device_core_interfaces import UsbEndpointInterface


class UsbDeviceEpBuffers(Unit):
    """
    USB device endpoint buffers
    Buffers for the data transfers which are between usb core and usb function.

    .. hwt-autodoc::
    """

    def _config(self) -> None:
        self.ENDPOINT_META: Tuple[Tuple[Optional[UsbEndpointMeta], Optional[UsbEndpointMeta]]] = Param(None)
        self.DATA_WIDTH = Param(8)

    def _declr(self) -> None:
        """
        :note: ep.rx = from host, ep.tx = to host
        """
        assert self.ENDPOINT_META is not None, "ENDPOINT_META parameter is required"
        addClkRstn(self)
        self.usb_core_io: UsbEndpointInterface = UsbEndpointInterface()
        eps = HObjList()
        for rx, tx in self.ENDPOINT_META:
            if rx is None and tx is None:
                ep = None
            else:
                ep = AxiStreamFullDuplex()
                ep.USE_KEEP = True
                ep.DATA_WIDTH = self.DATA_WIDTH
                ep.HAS_RX = rx is not None
                ep.HAS_TX = tx is not None
            eps.append(ep)

        self.ep: HObjList[AxiStreamFullDuplex] = eps

    def connect_rx_part(self, rx_channels: List[Tuple[int, AxiStream, UsbEndpointMeta, AxiSFifoDrop]]):
        if not rx_channels:
            assert not self.usb_core_io.HAS_RX
            return
        usb_endp = self.usb_core_io.endp
        sn = StreamNode(
            [self.usb_core_io.rx],
            [],  # added later
        )
        usb_rx = self.usb_core_io.rx
        for (ep_i, ep_rx, _, rx_fifo) in rx_channels:
            if rx_fifo is None:
                _rx = self.ep[ep_i].rx
                ep_rx(usb_rx, exclude=[usb_rx.ready, usb_rx.valid])
            else:
                _rx = rx_fifo.dataIn
                ep_rx(rx_fifo.dataOut)
                rx_fifo.dataIn(usb_rx, exclude=[usb_rx.ready, usb_rx.valid])
                # discard on rx error
                rx_fifo.dataIn_discard(usb_rx.valid & usb_rx.last & usb_rx.user)

            sn.slaves.append(_rx)
            sn.extraConds[_rx] = usb_endp.data._eq(ep_i)
            sn.skipWhen[_rx] = usb_endp.data != ep_i

        sn.sync(usb_endp.vld)

        self.usb_core_io.rx_stall(~In(usb_endp.data, [i for (i, _, _, _) in rx_channels]))

    def connect_tx_part(self, tx_channels: List[Tuple[int, AxiStream, UsbEndpointMeta, AxiSFifoCopy]]):
        if not tx_channels:
            assert not self.usb_core_io.HAS_TX
            return

        for (_, ep_tx, _, tx_fifo) in tx_channels:
            if tx_fifo is None:
                continue
            tx_fifo.dataIn(ep_tx)
            tx_fifo.dataOut_copy_frame(0)  # [todo]

        usb_endp = self.usb_core_io.endp
        tx = self.usb_core_io.tx
        Switch(usb_endp.data).add_cases(
            (i, tx(self.ep[i].tx if tx_fifo is None else tx_fifo.dataOut, exclude=[tx.ready, tx.valid])
            ) for (i, _, _, tx_fifo) in tx_channels
        ).Default(
            tx.data(None),
            tx.keep(None),
            tx.last(None),
        )
        sn = StreamNode(
            [],  # added later
            [tx],
        )
        for (i, _, _, tx_fifo) in tx_channels:
            if tx_fifo is None:
                _tx = self.ep[i].tx
            else:
                _tx = tx_fifo.dataOut
            sn.extraConds[_tx] = usb_endp.data._eq(i)
            sn.skipWhen[_tx] = usb_endp.data != i
            sn.masters.append(_tx)

        sn.sync(usb_endp.vld)
        # stall if there is no such a endpoint
        self.usb_core_io.tx_stall(~In(usb_endp.data, [i for (i, _, _, _) in tx_channels]))

    def _impl(self):
        rx_channels = []
        tx_channels = []
        rx_fifos = HObjList()
        tx_fifos = HObjList()
        for i, (ep, (rx_conf, tx_conf)) in enumerate(zip(self.ep, self.ENDPOINT_META)):
            if ep is None:
                continue
            if ep.HAS_RX:
                if rx_conf.buffer_size > 0:
                    rx_fifo = AxiSFifoDrop()
                    rx_fifo.USE_KEEP = True
                    rx_fifo.DATA_WIDTH = self.DATA_WIDTH
                    rx_fifo.DEPTH = rx_conf.buffer_size
                else:
                    rx_fifo = None

                rx_fifos.append(rx_fifo)
                rx_channels.append((i, ep.rx, rx_conf, rx_fifo))

            if ep.HAS_TX:
                if tx_conf.buffer_size > 0:
                    tx_fifo = AxiSFifoCopy()
                    tx_fifo.USE_KEEP = True
                    tx_fifo.DATA_WIDTH = self.DATA_WIDTH
                    tx_fifo.DEPTH = tx_conf.buffer_size
                else:
                    tx_fifo = None

                tx_fifos.append(tx_fifo)
                tx_channels.append((i, ep.tx, tx_conf, tx_fifo))

        self.rx_fifos = rx_fifos
        self.tx_fifos = tx_fifos
        self.connect_rx_part(rx_channels)
        self.connect_tx_part(tx_channels)

        propagateClkRstn(self)


if __name__ == "__main__":
    from hwtLib.peripheral.usb.descriptors.cdc import get_default_usb_cdc_vcp_descriptors
    from hwt.synthesizer.utils import to_rtl_str
    u = UsbDeviceEpBuffers()
    u.ENDPOINT_META = get_default_usb_cdc_vcp_descriptors().get_endpoint_meta()
    u.ENDPOINT_META[0][0].buffer_size = 0
    u.ENDPOINT_META[0][1].buffer_size = 0
    print(to_rtl_str(u))