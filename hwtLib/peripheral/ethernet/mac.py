#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import Or, If
from hwt.hdl.types.bits import HBits
from hwt.hdl.types.stream import HStream
from hwt.hdl.types.struct import HStruct
from hwt.hwIOs.std import HwIOVldSync
from hwt.hwIOs.utils import addClkRstn, propagateClkRstn
from hwt.hwModule import HwModule
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwtLib.amba.axi4s import Axi4Stream
from hwtLib.amba.axi4s_fullduplex import Axi4StreamFullDuplex
from hwtLib.amba.axis_comp.builder import Axi4SBuilder
from hwtLib.amba.axis_comp.fifoDrop import Axi4SFifoDrop
from hwtLib.amba.axis_comp.frame_deparser import Axi4S_frameDeparser
from hwtLib.amba.axis_comp.frame_parser import Axi4S_frameParser
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.logic.crc import Crc
from hwtLib.logic.crcPoly import CRC_32
from hwtLib.peripheral.ethernet._axis_eq import Axi4S_eq
from hwtLib.peripheral.ethernet.constants import ETH_BITRATE
from hwtLib.peripheral.ethernet.vldsynced_data_err_last import VldSyncedDataErrLast
from hwtLib.types.net.ethernet import eth_mac_t, eth_addr_parse

CRC32_RESIDUE = 0x2144df1c


def vldSyncedReg(parent: HwModule, hwIO: HwIOVldSync):
    reg = parent._reg(hwIO._name + "_reg", HStruct(
        *((cHwIO._dtype, cHwIO._name) for cHwIO in hwIO._hwIOs)
    ))
    for cHwIO in hwIO._hwIOs:
        getattr(reg, cHwIO._name)(cHwIO)
    return reg


class EthernetMac(HwModule):
    """
    Media independent Ethernet MAC (Media Access Control)
    Manages frame dropping, error handling and FCSs,
    rest (preamble, SFD, IPG, CDCs, PHY signal protocol, ...)
    is managed by adapter for specified PHY interface.

    :note: This component does not have any control registers or statistics etc.
        But the signals are accessible. Inherit from this class and
        add control bus, statistics, address space of of your choice.
        Same applies to a MAC address filter.
    :note: This component Ethernet MAC implementation is efficient for
        bandwidths where it is not required to send multiple packets in same clk tick.
        (usually 10M - 10G but depends on frequency and data width)

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.FREQ = HwParam(int(100e6))
        self.BITRATE = HwParam(ETH_BITRATE.M_100M)
        self.DATA_WIDTH = HwParam(8)
        self.DEFAULT_MAC_ADDR = HwParam("01:23:45:67:89:AB")
        self.HAS_TX = HwParam(True)
        self.HAS_RX = HwParam(True)
        # number of fifo items (size[B] = *DATA_WIDTH/8)
        self.RX_FIFO_DEPTH = HwParam(2048)

    @override
    def hwDeclr(self):
        addClkRstn(self)
        self.USE_KEEP = self.DATA_WIDTH > 8
        with self._hwParamsShared():
            if self.HAS_TX:
                self.phy_tx = Axi4Stream()._m()

            if self.HAS_RX:
                self.phy_rx = VldSyncedDataErrLast()

            self.eth = Axi4StreamFullDuplex()
            self.eth.USE_KEEP = self.USE_KEEP
            self.eth.IS_BIGENDIAN = True

    def _rx_mac_filter(self):
        def_mac = eth_addr_parse(self.DEFAULT_MAC_ADDR)
        def_mac = int.from_bytes(def_mac, 'little')
        mac_eq = Axi4S_eq()
        mac_eq._updateHwParamsFrom(self)
        mac_eq.VAL = eth_mac_t.from_py(def_mac)
        self.rx_mac_filter = mac_eq
        return mac_eq.dataIn, mac_eq.dataOut

    def _rx_logic(self):
        """
        Recieving of a frame takes at least these steps:
        * parse dst mac
        * check fcs
        * cut off fcs
        * store in output buffer

        The frame can be dropped if:
        * there is an error durig recieving on PHY/adapter layer (err_rx_phy)
        * or because of backpressure from eth.rx (err_rx_out_of_mem)
        * or because of incorrect FCS            (err_rx_bad_fcs)
        * or because of MAC address filter       (err_rx_not_my_mac)
        """
        fcs_bad = self.err_rx_fcs_bad = self._sig("err_rx_fcs_bad")
        fcs_good = self.err_rx_fcs_good = self._sig("err_rx_fcs_good")
        out_of_mem = self.err_rx_out_of_mem = self._sig("err_rx_out_of_mem")
        phy_err = self.err_rx_phy = self._sig("err_rx_phy")
        not_my_mac = self.err_rx_not_my_mac = self._sig("err_rx_not_my_mac")
        errors = [fcs_bad, out_of_mem, phy_err, not_my_mac]

        # dst mac is a stream because we want to resize it's channel
        # according to input interface so we do not waste resoruces
        # on buffers allong the way to output

        def propagate_config(u):
            u.DATA_WIDTH = self.DATA_WIDTH
            u.USE_KEEP = self.USE_KEEP

        dst_mac_parser = Axi4S_frameParser(HStruct(
            (HStream(eth_mac_t, frame_len=(1, 1)), "dst"),
            (HStream(HBits(8)), None),  # ignore data at the end
        ))
        propagate_config(dst_mac_parser)
        self.rx_mac_parser = dst_mac_parser

        fcs_cutter = Axi4S_frameParser(HStruct(
            (HStream(HBits(8)), "data"),
            (HBits(32), None),  # fcs to cut off
        ))
        propagate_config(fcs_cutter)
        self.tx_fcs_cutter = fcs_cutter

        # rcr checker
        crc = Crc()
        crc.setConfig(CRC_32)
        crc.MASK_GRANULARITY = 8
        crc.LATENCY = 0
        propagate_config(crc)
        self.rx_crc = crc

        # reg added in order to see more glitches in sim more clearly
        din = vldSyncedReg(self, self.phy_rx)

        in_sync = StreamNode(
            [],
            [dst_mac_parser.dataIn,
             fcs_cutter.dataIn])
        in_sync.sync(din.vld)
        for inp in (dst_mac_parser.dataIn,
                    fcs_cutter.dataIn,
                    crc.dataIn):
            inp.data(din.data)
            if self.USE_KEEP:
                if inp is crc.dataIn:
                    inp.mask(din.mask)
                else:
                    inp.keep(din.mask)
            inp.last(din.last)
        crc.dataIn.vld(din.vld)
        # drop fcs, was checked on original stream

        # output fifo for dropping of invalid frames
        out_fifo = Axi4SFifoDrop()
        out_fifo.DEPTH = self.RX_FIFO_DEPTH
        propagate_config(out_fifo)
        self.rx_out_fifo = out_fifo

        out_fifo.dataIn(fcs_cutter.dataOut.data)
        data = Axi4SBuilder(self, out_fifo.dataOut).buff(4).end

        err_in_this_frame = self._reg("rx_err_in_this_frame", def_val=0)
        fcs_good_in_this_frame = self._reg("rx_fcs_good_in_this_frame", def_val=0)
        If(data.valid & data.last,
           fcs_good_in_this_frame(0),
           err_in_this_frame(0),
        ).Else(
           fcs_good_in_this_frame(fcs_good_in_this_frame | fcs_good),
           err_in_this_frame(din.vld & Or(*errors))
        )
        out_fifo.dataIn_discard((din.vld & Or(*errors)) | err_in_this_frame)

        # postpone procesing of last word until we know the result of fcs check
        dout = self.eth.rx
        dout(data, exclude=[data.ready, data.valid])
        not_fcs_check_wait = ~data.valid | ~data.last | fcs_good_in_this_frame | err_in_this_frame
        StreamNode(
            [data], [dout],
        ).sync(not_fcs_check_wait)

        # errors and mac filter
        mac_filter_in, is_my_mac = self._rx_mac_filter()
        mac_filter_in(dst_mac_parser.dataOut.dst)
        is_my_mac.rd(1)
        not_my_mac(is_my_mac.vld & ~is_my_mac.data)
        phy_err(din.err & din.vld)
        fcs_good(din.vld & din.last & (crc.dataOut._eq(CRC32_RESIDUE)))
        fcs_bad(din.vld & din.last & (crc.dataOut != CRC32_RESIDUE))
        out_of_mem(~fcs_cutter.dataIn.ready & din.vld)
        propagateClkRstn(self)

    def _tx_logic(self):
        """
        Compute and append FCS, underflow error checking
        """
        # underflow = self.err_tx_underflow = self._sig("err_tx_underflow")
        Eth_frame_t = HStruct(
            (HStream(HBits(8)), "data"),
            (HBits(32), "fcs"),
        )

        deparser = Axi4S_frameDeparser(Eth_frame_t)
        crc = Crc()
        crc.setConfig(CRC_32)
        crc.MASK_GRANULARITY = 8
        crc.LATENCY = 0
        deparser.USE_STRB = self.USE_KEEP
        for c in (deparser, crc):
            c.DATA_WIDTH = self.DATA_WIDTH
        self.tx_crc = crc
        self.tx_frame_gen = deparser
        propagateClkRstn(self)
        crc.dataIn(self.eth.tx,
                exclude=[
                    self.eth.tx.ready,
                    self.eth.tx.valid,
                    crc.dataIn.vld,
                    crc.dataIn.rd,
                    *([self.eth.tx.keep,
                       crc.dataIn.mask,
                       ] if self.USE_KEEP else []),
                ]
        )
        deparser.dataIn.data(self.eth.tx,
                       exclude=[
                           self.eth.tx.ready,
                           self.eth.tx.valid,
                           *([self.eth.tx.keep,
                              deparser.dataIn.data.strb,
                              ] if self.USE_KEEP else []),
                       ]
        )
        StreamNode([self.eth.tx],
                   [crc.dataIn, deparser.dataIn.data]).sync()
        if self.USE_KEEP:
            deparser.dataIn.data.strb(self.eth.tx.keep)
            crc.dataIn.mask(self.eth.tx.keep)
        fcs_tmp = self._reg("fcs_tmp", crc.dataOut._dtype)
        fcs_vld = self._reg("fcs_vld", def_val=0)
        # [TODO] check if this is required in order to save mux
        If(crc.dataIn.vld & crc.dataIn.last,
            fcs_tmp(crc.dataOut),
            deparser.dataIn.fcs.data(crc.dataOut),
            fcs_vld(~deparser.dataIn.fcs.rd)
        ).Else(
            deparser.dataIn.fcs.data(fcs_tmp),
            If(deparser.dataIn.fcs.rd,
                fcs_vld(0),
            )
        )
        deparser.dataIn.fcs.vld(fcs_vld | (crc.dataIn.vld & crc.dataIn.last))

        self.phy_tx(deparser.dataOut, exclude=[self.phy_tx.keep, deparser.dataOut.strb, ] if self.USE_KEEP else None)
        if self.USE_KEEP:
            self.phy_tx.keep(deparser.dataOut.strb)

    @override
    def hwImpl(self):
        if self.HAS_RX:
            self._rx_logic()
        if self.HAS_TX:
            self._tx_logic()


if __name__ == "__main__":
    from hwt.synth import to_rtl_str

    m = EthernetMac()
    m.DATA_WIDTH = 16
    # m.HAS_TX = False
    # m.HAS_RX = False
    print(to_rtl_str(m))
