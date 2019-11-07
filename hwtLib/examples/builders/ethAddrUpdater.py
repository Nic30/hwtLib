#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.hdl.types.struct import HStruct
from hwt.hdl.types.structUtils import HStruct_selectFields
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.unit import Unit
from hwt.synthesizer.param import Param
from hwtLib.amba.axi3 import Axi3, Axi3_addr, Axi3_w
from hwtLib.amba.axi_comp.axi4_rDatapump import Axi_rDatapump
from hwtLib.amba.axi_comp.axi4_wDatapump import Axi_wDatapump
from hwtLib.amba.axi_comp.axi_datapump_utils import connectDp
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.structManipulators.structReader import StructReader
from hwtLib.structManipulators.structWriter import StructWriter
from hwtLib.types.net.eth import Eth2Header_t
from hwtLib.types.net.ip import IPv4Header_t


frameHeader = HStruct(
    (Eth2Header_t, "eth"),
    (IPv4Header_t, "ipv4")
    )
frameHeader = HStruct_selectFields(frameHeader,
                                   {"eth": {"src", "dst"},
                                    "ipv4": {"src", "dst"}
                                    })


class EthAddrUpdater(Unit):
    """
    This is example unit which reads dst and src addresses(MAC and IPv4)
    from ethernet frame stored in memory and writes this addresses
    in reverse direction into second frame.

    .. hwt-schematic::
    """
    def _config(self):
        Axi3._config(self)
        self.MAX_LEN = Param(8)

    def _declr(self):
        addClkRstn(self)

        with self._paramsShared():
            self.axi_m = Axi3()._m()

        a = self.packetAddr = Handshaked()
        a.DATA_WIDTH = self.ADDR_WIDTH

        with self._paramsShared():
            self.rxPacketLoader = StructReader(frameHeader)
            self.rxDataPump = Axi_rDatapump(Axi3_addr)

            self.txPacketUpdater = StructWriter(frameHeader)
            self.txDataPump = Axi_wDatapump(Axi3_addr, Axi3_w)
        for o in (self.txPacketUpdater, self.txDataPump):
            o.USE_STRB = True

    def _impl(self):
        propagateClkRstn(self)
        connectDp(self, self.rxPacketLoader, self.rxDataPump, self.axi_m)
        connectDp(self, self.txPacketUpdater, self.txDataPump, self.axi_m)

        self.txPacketUpdater.writeAck.rd(1)

        rxR = self.rxPacketLoader.dataOut
        txW = self.txPacketUpdater.dataIn

        def withFifo(interface):
            return HsBuilder(self, interface)\
                      .buff(items=4)\
                      .end

        txW.eth.dst(withFifo(rxR.eth.src))
        txW.eth.src(withFifo(rxR.eth.dst))

        txW.ipv4.dst(withFifo(rxR.ipv4.src))
        txW.ipv4.src(withFifo(rxR.ipv4.dst))

        HsBuilder(self, self.packetAddr).split_copy_to(
            self.rxPacketLoader.get,
            self.txPacketUpdater.set)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = EthAddrUpdater()
    print(toRtl(u))
