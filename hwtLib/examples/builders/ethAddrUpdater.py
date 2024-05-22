#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.types.struct import HStruct
from hwt.hdl.types.structUtils import HdlType_select
from hwt.hwIOs.std import HwIODataRdVld
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwParam import HwParam
from hwt.hwModule import HwModule
from hwtLib.amba.axi3 import Axi3
from hwtLib.amba.axi_comp.virtualDma import AxiVirtualDma
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.types.net.ethernet import Eth2Header_t
from hwtLib.types.net.ip import IPv4Header_t


frameHeader = HStruct(
    (Eth2Header_t, "eth"),
    (IPv4Header_t, "ipv4")
)

# filter out all except eth MACs and IPs
frameHeader = HdlType_select(
    frameHeader,
    {
        "eth": {"src", "dst"},
        "ipv4": {"src", "dst"}
    }
)


class EthAddrUpdater(HwModule):
    """
    This is example unit which reads dst and src addresses(MAC and IPv4)
    from ethernet frame stored in memory and writes this addresses
    in reverse direction into second frame.

    .. hwt-autodoc::
    """
    def _config(self):
        Axi3._config(self)
        self.ALIGNAS = HwParam(self.DATA_WIDTH)

    def _declr(self):
        addClkRstn(self)

        with self._hwParamsShared():
            self.axi_m = Axi3()._m()

        a = self.packetAddr = HwIODataRdVld()
        a.DATA_WIDTH = self.ADDR_WIDTH

    def _impl(self):
        dma = AxiVirtualDma(self.axi_m, alignas=self.ALIGNAS)
        rxGet, rxR = dma.read(frameHeader)
        txSet, txW, wAck = dma.write(frameHeader)
        dma.build()

        # send address to an engine which reads and writes the packet header
        HsBuilder(self, self.packetAddr)\
            .split_copy_to(rxGet, txSet)

        # ignore write ack
        wAck.rd(1)

        def withFifo(interface):
            return HsBuilder(self, interface)\
                      .buff(items=4)\
                      .end

        # swap dst/src in IP and Ethernet MAC, use fifo to compensate for
        # a diferent arrival times of the data
        txW.eth.dst(withFifo(rxR.eth.src))
        txW.eth.src(withFifo(rxR.eth.dst))

        txW.ipv4.dst(withFifo(rxR.ipv4.src))
        txW.ipv4.src(withFifo(rxR.ipv4.dst))

        propagateClkRstn(self)


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    
    m = EthAddrUpdater()
    print(to_rtl_str(m))
