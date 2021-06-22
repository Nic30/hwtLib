#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import ceil
from typing import Union, Optional

from hwt.code import If, Or
from hwt.hdl.types.bits import Bits
from hwt.hdl.types.struct import HStruct
from hwt.hdl.types.union import HUnion
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.math import log2ceil
from hwt.pyUtils.arrayQuery import iter_with_last
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.param import Param
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwtLib.abstract.busBridge import BusBridge
from hwtLib.abstract.busEndpoint import AddressStepTranslation
from hwtLib.amba.axi4 import Axi4, Axi4_addr
from hwtLib.amba.axi_comp.buff import AxiBuff
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.builder import AxiSBuilder
from hwtLib.amba.axis_comp.frame_deparser._deparser import AxiS_frameDeparser
from hwtLib.amba.constants import BURST_INCR, CACHE_DEFAULT, LOCK_DEFAULT, \
    BYTES_IN_TRANS, QOS_DEFAULT, PROT_DEFAULT
from hwtLib.common_nonstd_interfaces.addr_data_hs import AddrDataHs
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.handshaked.ramAsHs import RamHsR
from hwtLib.handshaked.reg import HandshakedReg
from hwtLib.handshaked.streamNode import StreamNode
from pyMathBitPrecise.bit_utils import mask, bit_field


@serializeParamsUniq
class AddrDataHs_to_Axi(BusBridge):
    """
    Bridge AddrDataHs,RamHsR -> Axi3/4

    * read delay: 1, transaction overlap 0
    * write delay: 1, transaction overlap 0

    :ivar ~.S_ADDR_STEP: number of bites per step on AddrDataHs,RamHsR interfaces
    :ivar ~.M_DATA_WIDTH: data width for AXI interface
    :ivar ~.M_ID_WIDTH: id width for AXI interface
    :ivar ~.M_ADDR_OFFSET: address offset value for axi interface

    .. hwt-autodoc:: example_AddrDataHs_to_Axi
    """

    def __init__(self, intfCls=Axi4, hdl_name_override:Optional[str]=None):
        self.intfCls = intfCls
        super(AddrDataHs_to_Axi, self).__init__(hdl_name_override=hdl_name_override)

    def _config(self):
        self.intfCls._config(self)
        self.S_ADDR_STEP = Param(64)
        self.S_ADDR_WIDTH = Param(self.ADDR_WIDTH)
        self.S_DATA_WIDTH = Param(self.DATA_WIDTH)
        self.M_ADDR_OFFSET = Param(0)
        self.MAX_TRANS_OVERLAP = Param(64)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared(prefix="S_"):
            if self.HAS_R:
                self.s_r = RamHsR()
            if self.HAS_W:
                self.s_w = AddrDataHs()

        with self._paramsShared():
            self.m = self.intfCls()._m()

        self.in_axi_t, self.data_words_in_axi_word = self.generate_in_axi_type()

    def generate_in_axi_type(self):
        s_w = self.s_w
        axi = self.m
        # type used to describe how to build and parse axi-s frames
        DW = ceil(s_w.DATA_WIDTH / 8) * 8
        data_words_in_axi_word = axi.DATA_WIDTH // DW
        if data_words_in_axi_word <= 1:
            data_type = HStruct(
                (Bits(DW), "data")
            )
        else:
            assert data_words_in_axi_word > 1, data_words_in_axi_word
            data_fields = []
            for last, i in iter_with_last(range(data_words_in_axi_word)):
                prefix, suffix = (), ()
                if i != 0:
                    prefix = ((Bits(i * DW), None),)
                if not last:
                    suffix = ((Bits(axi.DATA_WIDTH - ((i + 1) * DW)), None),)
                data_fields.append(
                    (HStruct(
                        *prefix,
                        (Bits(DW), "data"),
                        *suffix),
                     f"data{i:d}"))
            data_type = HStruct(
                # union with member for each data position in axi word
                (HUnion(*data_fields), 'data')
            )
        return data_type, data_words_in_axi_word

    def addr_defaults(self, a: Axi4_addr):
        axi = self.m
        a.id(0)
        a.burst(BURST_INCR)
        a.cache(CACHE_DEFAULT)
        words = ceil(self.S_DATA_WIDTH / axi.DATA_WIDTH)
        a.len(words - 1)
        a.lock(LOCK_DEFAULT)
        a.size(BYTES_IN_TRANS(axi.DATA_WIDTH // 8))
        a.prot(PROT_DEFAULT)
        if hasattr(a, "qos"):
            # axi4
            a.qos(QOS_DEFAULT)

    def connect_addr(self, src, dst):
        AXI_ADDR_STEP = self.m._getAddrStep()  # naturally 8b
        addr_transl = AddressStepTranslation(self.S_ADDR_STEP, AXI_ADDR_STEP)
        return addr_transl.propagate(
            src, dst, dst_offset=self.M_ADDR_OFFSET)

    def connect_r(self, s_r: RamHsR, axi: Axi4, r_cntr: RtlSignal,
                  CNTR_MAX:int, in_axi_t: Union[HStruct, HUnion]):
        self.addr_defaults(axi.ar)

        # rm id from r channel as it is not currently supported in frame parser
        r_tmp = AxiStream()
        r_tmp.USE_STRB = False
        r_tmp.DATA_WIDTH = axi.r.DATA_WIDTH
        self.r_tmp = r_tmp
        r_tmp(axi.r, exclude=(axi.r.id, axi.r.resp, ))
        r_data = AxiSBuilder(self, r_tmp)\
            .parse(in_axi_t).data

        if self.data_words_in_axi_word <= 1:
            self.connect_addr(s_r.addr.data, axi.ar.addr)

            s_r.data.data(r_data.data[s_r.DATA_WIDTH:])

            ar_sn = StreamNode([s_r.addr], [axi.ar])
            r_sn = StreamNode([r_data], [s_r.data])

        else:
            addr, sub_addr = self.split_subaddr(s_r.addr.data)
            self.connect_addr(addr, axi.ar.addr)

            sel = HsBuilder(self, r_data._select, master_to_slave=False)\
                .buff(self.MAX_TRANS_OVERLAP).end
            sel.data(sub_addr)

            data_items = [getattr(r_data, f"data{i:d}").data for i in range(self.data_words_in_axi_word)]
            r_data_selected = HsBuilder.join_prioritized(self, data_items).end
            s_r.data.data(r_data_selected.data)

            ar_sn = StreamNode([s_r.addr], [axi.ar, sel])
            r_sn = StreamNode([r_data_selected], [s_r.data])

        ar_sn.sync(r_cntr != CNTR_MAX)
        r_sn.sync()
        r_en = r_sn.ack()
        If(axi.ar.ready & axi.ar.valid,
            If(~r_en,
               r_cntr(r_cntr + 1)
            )
        ).Elif(r_en,
            r_cntr(r_cntr - 1)
        )

    def split_subaddr(self, addr: RtlSignal):
        assert self.data_words_in_axi_word > 1, "Should be called only if there are multiple data words in single axi word"
        in_word_sub_addr_bits = log2ceil(self.data_words_in_axi_word - 1)
        main_addr = addr & bit_field(in_word_sub_addr_bits, addr._bit_length())
        sub_addr = addr[in_word_sub_addr_bits:]
        return main_addr, sub_addr

    def connect_w(self, s_w: AddrDataHs, axi: Axi4, w_cntr: RtlSignal, CNTR_MAX:int, in_axi_t: HStruct):

        def axi_w_deparser_parametrization(u: AxiS_frameDeparser):
            # [TODO] specify _frames or maxFrameLen if required (AXI3 16beats, AXI4 256)
            u.DATA_WIDTH = axi.DATA_WIDTH
            u.ID_WIDTH = 0

        # component to create a axi-stream like packet from AddrDataHs write data
        w_builder, w_in = AxiSBuilder.deparse(
            self, in_axi_t, Axi4.W_CLS,
            axi_w_deparser_parametrization)
        w_in = w_in.data

        self.addr_defaults(axi.aw)

        if self.data_words_in_axi_word <= 1:
            self.connect_addr(s_w.addr, axi.aw.addr)
            w_in.data(s_w.data, fit=True)
            aw_sn = StreamNode([s_w], [axi.aw, w_in])
        else:
            addr, sub_addr = self.split_subaddr(s_w.addr)
            self.connect_addr(addr, axi.aw.addr)
            w_in._select.data(sub_addr)

            # sel = HsBuilder(self, w_in._select, master_to_slave=False)\
            #     .buff(self.MAX_TRANS_OVERLAP).end
            # sel.data(sub_addr)

            w_reg = HandshakedReg(Handshaked)
            w_reg.DATA_WIDTH = s_w.DATA_WIDTH
            self.w_data_reg = w_reg
            w_reg.dataIn.data(s_w.data)

            aw_sn = StreamNode(
                [s_w],
                [axi.aw, w_reg.dataIn, w_in._select])

            data_items = [getattr(w_in, f"data{i:d}").data for i in range(self.data_words_in_axi_word)]
            for w in data_items:
                w.vld(w_reg.dataOut.vld)
                w.data(w_reg.dataOut.data)
                # ready is not important because it is part of  ._select.rd
            w_reg.dataOut.rd(Or(*[d.rd for d in data_items]))

        w_start_en = w_cntr != CNTR_MAX
        aw_sn.sync(w_start_en)
        # s_w.rd(win.rd)
        # axi.aw.valid(s_w.vld & w_start_en & ~waiting_for_w_data & win.rd)
        # win.vld(s_w.vld & w_start_en & axi.aw.ready)

        if hasattr(axi.w, "id"):
            # axi3
            axi.w(w_builder.end, exclude={axi.w.id})
            axi.w.id(0)
        else:
            # axi4
            axi.w(w_builder.end)

        If(axi.aw.ready & axi.aw.valid,
            If(~axi.b.valid,
               w_cntr(w_cntr + 1)
            )
        ).Elif(axi.b.valid,
            w_cntr(w_cntr - 1)
        )

        axi.b.ready(1)

    def _impl(self):
        S_ADDR_STEP = self.S_ADDR_STEP
        assert S_ADDR_STEP >= self.S_DATA_WIDTH, \
            (S_ADDR_STEP, self.S_DATA_WIDTH)

        axi = self.m
        # if 2 * self.S_ADDR_STEP <= self.DATA_WIDTH:
        #    # multiple items can be in a single axi word
        #    # require the transaction alignment
        #    axi_resize = AxiResize(axi.__class__)
        #    axi_resize._updateParamsFrom(axi)
        #    axi_resize.DATA_WIDTH = self.S_ADDR_STEP
        #    axi_resize.OUT_DATA_WIDTH = axi.DATA_WIDTH
        #    axi_resize.OUT_ADDR_WIDTH = axi.ADDR_WIDTH
        #    self.axi_resize = axi_resize
        #    axi(axi_resize.m)
        #    axi = axi_resize.s

        # add extra register on axi
        b = AxiBuff(axi.__class__)
        b._updateParamsFrom(axi)
        self.axi_buff = b
        axi(b.m)
        axi = b.s

        cntr_t = Bits(log2ceil(self.MAX_TRANS_OVERLAP), signed=False)
        CNTR_MAX = mask(cntr_t.bit_length())

        if self.HAS_R:
            s_r = self.s_r
            r_cntr = self._reg("r_cntr", cntr_t, def_val=0)
            self.connect_r(s_r, axi, r_cntr, CNTR_MAX, self.in_axi_t)

        if self.HAS_W:
            s_w = self.s_w
            w_cntr = self._reg("w_cntr", cntr_t, def_val=0)
            self.connect_w(s_w, axi, w_cntr, CNTR_MAX, self.in_axi_t)

        propagateClkRstn(self)


def example_AddrDataHs_to_Axi():
    """
    Download a 512b word over 64b interface
    """
    u = AddrDataHs_to_Axi()
    # u.ADDR_WIDTH = 32
    # u.DATA_WIDTH = 64
    # u.S_ADDR_WIDTH = 4
    # u.S_ADDR_STEP = 512
    # u.S_DATA_WIDTH = 512
    # u.M_ADDR_OFFSET = 99

    # u.ADDR_WIDTH = 16 + 2
    # u.S_ADDR_WIDTH = 16
    # # in each axi word there is only lower half used
    # u.DATA_WIDTH = u.S_DATA_WIDTH = u.S_ADDR_STEP = 32
    # u.M_ADDR_OFFSET = 0

    u.S_ADDR_WIDTH = 16 - 1
    u.ADDR_WIDTH = 16
    # in each axi word there is only lower half used
    u.DATA_WIDTH = 32
    u.S_DATA_WIDTH = u.S_ADDR_STEP = 16
    u.M_ADDR_OFFSET = 0

    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = example_AddrDataHs_to_Axi()

    print(to_rtl_str(u))
