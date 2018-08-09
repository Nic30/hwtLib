#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import If, Concat, log2ceil, Switch
from hwt.hdl.types.bits import Bits
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.vectorUtils import iterBits
from hwtLib.handshaked.compBase import HandshakedCompBase
from hwtLib.handshaked.reg import HandshakedReg


class HsResizer(HandshakedCompBase):
    """
    Resize width of handshaked interface
    """
    def __init__(self, hsIntfCls, scale, inIntfConfigFn, outIntfConfigFn):
        """
        :param hsIntfCls: class of interface which should be used as interface of this unit
        :param scale: tuple (in scale, out scale) one of scales has to be 1, f. e. (1,2) means output
            will be 2x wider
        :param inIntfConfigFn: function inIntfConfigFn(input interface) which will be applied on dataIn
        :param outIntfConfigFn: function outIntfConfigFn(input interface) which will be applied on dataOut
        """
        HandshakedCompBase.__init__(self, hsIntfCls)

        assert len(scale) == 2
        scale = (int(scale[0]), int(scale[1]))
        assert scale[0] == 1 or scale[1] == 1
        assert scale[0] > 0 and scale[1] > 0

        self._scale = scale

        self._inIntfConfigFn = inIntfConfigFn
        self._outIntfConfigFn = outIntfConfigFn

    def _config(self):
        pass

    def _declr(self):
        addClkRstn(self)
        self.dataIn = self.intfCls()
        self._inIntfConfigFn(self.dataIn)

        self.dataOut = self.intfCls()
        self._outIntfConfigFn(self.dataOut)

    def _upscaleDataPassLogic(self, inputRegs_cntr, ITEMS):

        # valid when all registers are loaded and input with last datapart is valid 
        self.getVld(self.dataOut)(inputRegs_cntr._eq(ITEMS - 1) & self.getVld(self.dataIn))

        self.getRd(self.dataIn)((inputRegs_cntr != ITEMS) | self.getRd(self.dataOut))
        If(inputRegs_cntr._eq(ITEMS - 1),
            If(self.getVld(self.dataIn) & self.getRd(self.dataOut),
               inputRegs_cntr(0)
            )
        ).Else(
            If(self.getVld(self.dataIn),
               inputRegs_cntr(inputRegs_cntr + 1)
            )
        )

    def _upscale(self, factor):
        inputRegs_cntr = self._reg("inputRegs_cntr",
                                   Bits(log2ceil(factor + 1), False),
                                   defVal=0)

        for din, dout in zip(self.getData(self.dataIn), self.getData(self.dataOut)):
            inputRegs = [self._reg("inReg%d_%s" % (i, din._name), din._dtype)
                            for i in range(factor - 1) ]
            # last word will be passed directly

            for i, r in enumerate(inputRegs):
                If(inputRegs_cntr._eq(i) & self.getVld(self.dataIn),
                   r(din)
                )
            dout(Concat(din, *reversed(inputRegs)))

        self._upscaleDataPassLogic(inputRegs_cntr, factor)

    def _downscale(self, factor):
        inputRegs_cntr = self._reg("inputRegs_cntr",
                                   Bits(log2ceil(factor + 1), False),
                                   defVal=0)

        # instantiate HandshakedReg, handshaked builder is not used to avoid dependencies
        inReg = HandshakedReg(self.intfCls)
        inReg._updateParamsFrom(self.dataIn)
        self.inReg = inReg
        inReg.clk(self.clk)
        inReg.rst_n(self.rst_n)
        inReg.dataIn(self.dataIn)
        dataIn = inReg.dataOut
        dataOut = self.dataOut

        # create output mux
        for din, dout in zip(self.getData(dataIn), self.getData(dataOut)):
            widthOfPart = din._dtype.bit_length() // factor
            inParts = iterBits(din, bitsInOne=widthOfPart)
            Switch(inputRegs_cntr).addCases(
                [(i, dout(inPart)) for i, inPart in enumerate(inParts)]
                )

        self.getVld(dataOut)(self.getVld(dataIn))
        self.getRd(dataIn)(inputRegs_cntr._eq(factor - 1) & self.getRd(dataOut))

        If(self.getVld(dataIn) & self.getRd(dataOut),
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


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    from hwt.interfaces.std import Handshaked
    u = HsResizer(Handshaked,
                  [1, 3],
                  lambda intf: intf.DATA_WIDTH.set(32),
                  lambda intf: intf.DATA_WIDTH.set(3 * 32))
    print(toRtl(u))
