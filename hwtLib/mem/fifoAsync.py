#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Concat
from hwt.constraints import set_false_path, get_clock_of, set_max_delay
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.std import HwIOClk, HwIORst_n, HwIOFifoWriter, HwIOFifoReader
from hwt.math import log2ceil, isPow2
from hwt.serializer.mode import serializeParamsUniq
from hwt.hwParam import HwParam
from hwtLib.clocking.cdc import SignalCdcBuilder
from hwtLib.logic.cntrGray import binToGray
from hwtLib.mem.fifo import Fifo


@serializeParamsUniq
class FifoAsync(Fifo):
    """
    Asynchronous FIFO using BRAM/LUT memory, based on:
    * https://github.com/ZipCPU/website/blob/master/examples/afifo.v
    * https://github.com/alexforencich/verilog-axis/blob/master/rtl/axis_async_fifo.v

    .. hwt-autodoc:: _example_FifoAsync
    """

    def hwConfig(self):
        Fifo.hwConfig(self)
        self.IN_FREQ = HwParam(int(100e6))
        self.OUT_FREQ = HwParam(int(100e6))

    def hwDeclr(self):
        assert int(self.DEPTH) > 0, "FifoAsync is disabled in this case, do not use it entirely"
        assert isPow2(self.DEPTH), f"DEPTH has to be power of 2, is {self.DEPTH:d}"
        # pow 2 because of gray counter counters

        if self.EXPORT_SIZE or self.EXPORT_SPACE:
            raise NotImplementedError()

        self.dataIn_clk = HwIOClk()
        self.dataIn_clk.FREQ = self.IN_FREQ
        self.dataOut_clk = HwIOClk()
        self.dataOut_clk.FREQ = self.OUT_FREQ

        with self._hwParamsShared():
            with self._associated(clk=self.dataIn_clk):
                self.dataIn_rst_n = HwIORst_n()
                with self._associated(rst=self.dataIn_rst_n):
                    self.dataIn = HwIOFifoWriter()

            with self._associated(clk=self.dataOut_clk):
                self.dataOut_rst_n = HwIORst_n()
                with self._associated(rst=self.dataOut_rst_n):
                    self.dataOut = HwIOFifoReader()._m()
        self.AW = log2ceil(self.DEPTH)

    def _addr_reg_and_cdc(self, reg_name, clk_in, clk_out):
        """
        Create a register for head/tail FIFO reader/writter position
        with gray encoded value propagated to other clock domain
        """
        AW = self.AW
        gray_t = HBits(AW + 1)
        index_t = HBits(AW + 1)

        reg_bin = self._reg(reg_name + "_bin", index_t, def_val=0, **clk_in)
        reg_gray = self._reg(reg_name + "_gray", gray_t, def_val=0, **clk_in)
        cdc_builder = SignalCdcBuilder(
            reg_gray,
            (clk_in["clk"], clk_in["rst"]),
            (clk_out["clk"], clk_out["rst"]),
            reg_init_val=0)
        for _ in range(2):
            cdc_builder.add_out_reg()
        reg_gray(binToGray(reg_bin._rtlNextSig))
        reg_gray_out_clk = cdc_builder.path[-1]

        # because vivado generates _replica of reg_bin and reworks the gray register
        set_max_delay(reg_bin, cdc_builder.path[1], cdc_builder.META_PERIOD_NS)
        return reg_bin, reg_gray, reg_gray_out_clk

    def hwImpl(self):
        AW = self.AW
        din = self.dataIn
        dout = self.dataOut

        # store clock/resets to a tuples and dicts for later use
        clk_in = {"clk": self.dataIn_clk, "rst": self.dataIn_rst_n}
        clk_out = {"clk": self.dataOut_clk, "rst": self.dataOut_rst_n}

        # head/tail fifo pointers in gray/bin encoding with CDC
        r_bin, r_gray, r_gray_in_clk = self._addr_reg_and_cdc(
            "r", clk_out, clk_in)
        w_bin, w_gray, w_gray_out_clk = self._addr_reg_and_cdc(
            "w", clk_in, clk_out)

        w_full = self._reg("w_full", def_val=0, **clk_in)
        # wbin - rbin == 2^Nl https://zipcpu.com/blog/2018/07/06/afifo.html
        # first two bits inverted, rest equal
        w_full(w_gray._rtlNextSig._eq(Concat(~r_gray_in_clk[AW + 1:AW - 1],
                                       r_gray_in_clk[AW - 1:])))
        din.wait(w_full)
        w_en = din.en & ~w_full
        If(w_en,
           w_bin(w_bin + 1)
        )
        if self.DATA_WIDTH:
            memory_t = HBits(self.DATA_WIDTH)[self.DEPTH]
            memory = self._sig("memory", memory_t)
            If(clk_in["clk"]._onRisingEdge(),
               If(w_en,
                  memory[w_bin[AW:]](din.data)
               )
            )

        r_empty = self._reg("r_empty", def_val=1, **clk_out)
        r_empty(r_gray._rtlNextSig._eq(w_gray_out_clk))
        dout.wait(r_empty)
        r_en = dout.en & ~r_empty
        If(r_en,
           r_bin(r_bin + 1)
        )

        if self.DATA_WIDTH:
            r_reg = self._reg("r_reg", dout.data._dtype, **clk_out)
            # set_false_path dataIn_clk -> r_reg
            set_false_path(get_clock_of(w_bin), r_reg)
            If(r_en,
               r_reg(memory[r_bin[AW:]])
            )
            dout.data(r_reg)
        # dout.data(memory[r_bin[AW:]])


def _example_FifoAsync():
    m = FifoAsync()
    m.DEPTH = 4
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    
    m = _example_FifoAsync()
    print(to_rtl_str(m))
