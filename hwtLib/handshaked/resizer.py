#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Concat, Switch
from hwt.hdl.types.bits import HBits
from hwt.hwIOs.utils import addClkRstn
from hwt.math import log2ceil
from hwt.synthesizer.vectorUtils import iterBits
from hwtLib.handshaked.compBase import HandshakedCompBase
from hwtLib.handshaked.reg import HandshakedReg
from hwt.hwIOs.std import HwIORdVldSync
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwt.hwIO import HwIO


class HsResizer(HandshakedCompBase):
    """
    Resize width of handshaked interface

    .. hwt-autodoc:: _example_HsResizer
    """

    def __init__(self, hshwIO: HwIORdVldSync, scale, inHwIOConfigFn, outHwIOConfigFn):
        """
        :param hshwIO: class of interface which should be used
            as interface of this unit
        :param scale: tuple (in scale, out scale) one of scales has to be 1,
            f. e. (1,2) means output will be 2x wider
        :param inHwIOConfigFn: function inHwIOConfigFn(input interface)
            which will be applied on dataIn
        :param outHwIOConfigFn: function outHwIOConfigFn(input interface)
            which will be applied on dataOut
        """
        HandshakedCompBase.__init__(self, hshwIO)

        assert len(scale) == 2
        scale = (int(scale[0]), int(scale[1]))
        assert scale[0] == 1 or scale[1] == 1
        assert scale[0] > 0 and scale[1] > 0

        self._scale = scale

        self._inIntfConfigFn = inHwIOConfigFn
        self._outIntfConfigFn = outHwIOConfigFn

    def _config(self):
        pass

    def _declr(self):
        addClkRstn(self)
        self.dataIn = self.hwIOCls()
        self._inIntfConfigFn(self.dataIn)

        self.dataOut = self.hwIOCls()._m()
        self._outIntfConfigFn(self.dataOut)

    def _upscaleDataPassLogic(self, inputRegs_cntr: RtlSignal, ITEMS: int):

        # valid when all registers are loaded and input with last datapart is valid
        vld = self.get_valid_signal
        rd = self.get_ready_signal
        vld(self.dataOut)(inputRegs_cntr._eq(ITEMS - 1) & vld(self.dataIn))

        rd(self.dataIn)((inputRegs_cntr != ITEMS) | rd(self.dataOut))
        If(inputRegs_cntr._eq(ITEMS - 1),
            If(vld(self.dataIn) & rd(self.dataOut),
               inputRegs_cntr(0)
            )
        ).Else(
            If(vld(self.dataIn),
               inputRegs_cntr(inputRegs_cntr + 1)
            )
        )

    def _upscale(self, factor: int):
        inputRegs_cntr = self._reg("inputRegs_cntr",
                                   HBits(log2ceil(factor + 1), False),
                                   def_val=0)

        for din, dout in zip(self.get_data(self.dataIn),
                             self.get_data(self.dataOut)):
            inputRegs = [self._reg(f"inReg{i:d}_{din._name:s}", din._dtype)
                         for i in range(factor - 1)]
            # last word will be passed directly

            for i, r in enumerate(inputRegs):
                If(inputRegs_cntr._eq(i) & self.get_valid_signal(self.dataIn),
                   r(din)
                )
            dout(Concat(din, *reversed(inputRegs)))

        self._upscaleDataPassLogic(inputRegs_cntr, factor)

    def _downscale(self, factor: int):
        inputRegs_cntr = self._reg("inputRegs_cntr",
                                   HBits(log2ceil(factor + 1), False),
                                   def_val=0)

        # instantiate HandshakedReg, handshaked builder is not used to avoid dependencies
        inReg = HandshakedReg(self.hwIOCls)
        inReg._updateParamsFrom(self.dataIn)
        self.inReg = inReg
        inReg.clk(self.clk)
        inReg.rst_n(self.rst_n)
        inReg.dataIn(self.dataIn)
        dataIn = inReg.dataOut
        dataOut = self.dataOut

        # create output mux
        for din, dout in zip(self.get_data(dataIn), self.get_data(dataOut)):
            widthOfPart = din._dtype.bit_length() // factor
            inParts = iterBits(din, bitsInOne=widthOfPart)
            Switch(inputRegs_cntr).add_cases(
                [(i, dout(inPart)) for i, inPart in enumerate(inParts)]
                )
        vld = self.get_valid_signal
        rd = self.get_ready_signal
        vld(dataOut)(vld(dataIn))
        self.get_ready_signal(dataIn)(inputRegs_cntr._eq(factor - 1) & rd(dataOut))

        If(vld(dataIn) & rd(dataOut),
            If(inputRegs_cntr._eq(factor - 1),
               inputRegs_cntr(0)
            ).Else(
               inputRegs_cntr(inputRegs_cntr + 1)
            )
        )

    def _impl(self):
        scale = self._scale
        if scale[0] > scale[1]:
            self._downscale(scale[0])
        elif scale[0] < scale[1]:
            self._upscale(scale[1])
        else:
            self.dataOut(self.dataIn)
            return


def _example_HsResizer():
    from hwt.hwIOs.std import HwIODataRdVld

    def set_dw_in(hwIO:HwIO):
        hwIO.DATA_WIDTH = 32

    def set_dw_out(hwIO:HwIO):
        hwIO.DATA_WIDTH = 3 * 32

    m = HsResizer(HwIODataRdVld,
                  [1, 3],
                  set_dw_in,
                  set_dw_out)
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str

    m = _example_HsResizer()
    print(to_rtl_str(m))
