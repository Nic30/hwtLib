#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from math import ceil

from hwt.code import Concat, Or, If
from hwt.code_utils import rename_signal
from hwt.hdl.constants import WRITE, READ
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import BramPort_withoutClk, HandshakeSync, VectSignal, \
    Signal
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.pyUtils.arrayQuery import iter_with_last
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.synthesizer.vectorUtils import iterBits
from hwtLib.mem.ram import RamSingleClock
from ipCorePackager.constants import DIRECTION
from pyMathBitPrecise.bit_utils import mask


class BramPort_withReadMask_withoutClk(BramPort_withoutClk):
    """
    Block RAM port with a :py:obj:`~en` handshaked interface for arbitration

    :ivar do_accumulate: Signal if 1 the mask bits are or-ed together with the value in stored in ram
    :ivar do_overwrite: Signal if 1 the the data mask in ram is set to current we value
    :note: :py:obj:`~.do_overwrite` has higher priority than :py:obj:`~.do_accumulate`
    :note: :py:obj:`~.do_accumulate` affect only the bytes in memory
        where data validity mask is stored.
    :ivar dout_mask: Read port contains this signal which contains
        the cumulative validity mask for the data.
    :note: en is related to a address, and write data, the read data
        may be available in nect clock cycle depending on read latency of the RAM

    .. hwt-autodoc::
    """

    def _declr(self):
        assert self.HAS_R or self.HAS_W, "has to have at least read or write part"

        self.addr = VectSignal(self.ADDR_WIDTH)
        DATA_WIDTH = self.DATA_WIDTH
        if self.HAS_W:
            self.din = VectSignal(DATA_WIDTH)

        if self.HAS_R:
            self.dout = VectSignal(DATA_WIDTH, masterDir=DIRECTION.IN)

        self.en = HandshakeSync()
        if (self.HAS_R and self.HAS_W) or (self.HAS_W and self.HAS_BE):
            # in write only mode we do not need this as well as we can use "en"
            if self.HAS_BE:
                assert DATA_WIDTH % 8 == 0, DATA_WIDTH
                self.we = VectSignal(DATA_WIDTH // 8)
            else:
                self.we = Signal()

        if self.HAS_W and self.HAS_BE:
            self.do_accumulate = Signal()
            self.do_overwrite = Signal()

        if self.HAS_R and self.HAS_BE:
            assert self.DATA_WIDTH % 8 == 0
            self.dout_mask = VectSignal(self.DATA_WIDTH // 8, masterDir=DIRECTION.IN)


def is_mask_byte_unaligned(mask_signal: RtlSignal) -> RtlSignal:
    # True if each byte of the mask is all 0 or all 1
    we_bytes = list(iterBits(mask_signal, bitsInOne=8, fillup=True))
    write_mask_not_aligned = []
    for last, b in iter_with_last(we_bytes):
        if last:
            # cut off padding if required
            mask_rem_w = mask_signal._dtype.bit_length() % 8
            if mask_rem_w:
                b = b[mask_rem_w:]
        write_mask_not_aligned.append((b != 0) & (b != mask(b._dtype.bit_length())))
    return Or(*write_mask_not_aligned)


class RamCumulativeMask(RamSingleClock):
    """
    RAM which stores also byte enable value for each data word (to keep track of which bytes were updated).

    :note: :class:`~.BramPort_withReadMask_withoutClk` contains the informations
        about how to control this component.
    """
    PORT_CLS = BramPort_withReadMask_withoutClk

    def _config(self):
        super(RamCumulativeMask, self)._config()
        self.HAS_BE = True
        self.PORT_CNT = (WRITE, READ)

    def _declr(self):
        assert self.HAS_BE
        assert len(self.PORT_CNT) >= 2, "Requres at least 1 WRITE and 1 READ port"
        assert self.PORT_CNT == (
            WRITE,
            *(READ for _ in range(len(self.PORT_CNT) - 1))),\
            self.PORT_CNT
        addClkRstn(self)
        RamSingleClock._declr_ports(self)

        self.MASK_W = self.DATA_WIDTH // 8
        # padding to make mask width % 8 == 0
        self.MASK_PADDING_W = ceil(self.MASK_W / 8) * 8 - self.MASK_W
        with self._paramsShared(exclude=({"DATA_WIDTH"}, {})):
            ram = self.ram = RamSingleClock()
            ram.DATA_WIDTH = self.DATA_WIDTH + self.MASK_PADDING_W + self.MASK_W

    def _impl(self):
        w = self.port[0]
        ram_w = self.ram.port[0]

        # True if each byte of the mask is 0xff or 0x00
        we_bytes = list(iterBits(w.we, bitsInOne=8, fillup=True))
        # cut off padding
        we_for_we_bytes = []
        for last, b in iter_with_last(we_bytes):
            if last and self.MASK_PADDING_W:
                mask_rem_w = self.MASK_W % 8
                b = b[mask_rem_w:]
            we_for_we_bytes.append(b != 0)

        we_for_we_bytes = rename_signal(
            self,
            Concat(*[b | ~w.do_accumulate | w.do_overwrite
                     for b in reversed(we_for_we_bytes)]),
            "we_for_we_bytes")

        preload = self._reg("preload", def_val=0)
        If(w.en.vld,
           preload(~preload & w.do_accumulate & ~w.do_overwrite)
        )
        w.en.rd(~w.do_accumulate | w.do_overwrite | preload)
        ram_w.addr(w.addr)
        ram_w.en(w.en.vld & (w.do_overwrite | ~w.do_accumulate | preload))
        ram_w.we(Concat(w.we, we_for_we_bytes))
        w_mask = w.we
        if self.MASK_PADDING_W:
            w_mask = Concat(Bits(self.MASK_PADDING_W).from_py(0), w_mask)

        is_first_read_port = True
        for ram_r, r in zip(self.ram.port[1:], self.port[1:]):
            if is_first_read_port:
                w_mask = preload._ternary(w_mask | ram_r.dout[self.MASK_PADDING_W + self.MASK_W:], w_mask)
                w_mask = rename_signal(self, w_mask, "w_mask")
                ram_w.din(Concat(w.din, w_mask))

                will_preload_for_accumulate = rename_signal(
                    self, w.en.vld & w.do_accumulate & ~w.do_overwrite, "will_preload_for_accumulate")
                ram_r.addr(will_preload_for_accumulate._ternary(w.addr, r.addr))
                ram_r.en(will_preload_for_accumulate | r.en.vld)
                # [TODO] check if r.en.rd is according to spec
                r.en.rd(~will_preload_for_accumulate | preload)
                is_first_read_port = False
            else:
                ram_r.addr(r.addr)
                ram_r.en(r.en.vld)
                r.en.rd(1)

            r.dout(ram_r.dout[:self.MASK_PADDING_W + self.MASK_W])
            r.dout_mask(ram_r.dout[self.MASK_W:])

        propagateClkRstn(self)


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    # from hwtLib.xilinx.constants import XILINX_VIVADO_MAX_DATA_WIDTH

    u = RamCumulativeMask()
    # u.ADDR_WIDTH = 5
    # u.DATA_WIDTH = 512
    # u.MAX_BLOCK_DATA_WIDTH = XILINX_VIVADO_MAX_DATA_WIDTH

    print(to_rtl_str(u))
