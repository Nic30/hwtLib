from hwt.code import If, log2ceil, Concat, Switch
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.param import Param, evalParam
from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.handshaked.streamNode import streamAck
from hwtLib.amba.axis_comp.builder import AxiSBuilder
from hwt.serializer.simModel.serializer import SimModelSerializer


class AxiS_resizer(AxiSCompBase):
    """
    Change data with of interface
    :attention: start of frame is expected to be aligned on first word
    :attention: strb can be not fully set only in last word
    :attention: in upscale mode id and other signals which are not dependent on data width
        are propagated only from last word
    :attention: in downscale mode strb does not affect if word should be send this means that
        there can be words with strb=0 if strb of input is ton fully set
    """
    def _config(self):
        AxiSCompBase._config(self)
        self.OUT_DATA_WIDTH = Param(64)

    def _declr(self):
        addClkRstn(self)

        with self._paramsShared():
            self.dataIn = self.intfCls()

        with self._paramsShared(exclude=[self.DATA_WIDTH]):
            self.dataOut = self.intfCls()
            self.dataOut._replaceParam("DATA_WIDTH", self.OUT_DATA_WIDTH)

    def nextAreNotValidLogic(self, inStrb, actualItemIndx, ITEMS, ITEM_DW):
        res = None
        ITEM_W = ITEM_DW//8
        for i in range(ITEMS - 1):  # -1 because if it is last we do not need this
            strbHi = ITEMS * ITEM_W
            strbLo = (i + 1) * ITEM_W
            othersNotValid = actualItemIndx._eq(i) & inStrb[strbHi:strbLo]._eq(0)
            #print(i, othersNotValid)
            if res is None:
                res = othersNotValid
            else:
                res = res | othersNotValid
        if res is None:
            #print(True)
            return True

        _res = self._sig("nextAreNotValid")
        _res ** res
        return _res

    def upscale(self, IN_DW, OUT_DW):
        if OUT_DW % IN_DW != 0:
            raise NotImplementedError()
        ITEMS = OUT_DW // IN_DW
        dIn = self.getDataWidthDependent(self.dataIn)

        dataOut = self.dataOut 
        dOut = self.getDataWidthDependent(dataOut)

        itemCntr = self._reg("itemCntr", vecT(log2ceil(ITEMS + 1)), defVal=0)
        hs = streamAck([self.dataIn], [dataOut])
        isLastItem = (itemCntr._eq(ITEMS - 1) | self.dataIn.last)

        vld = self.getVld(self.dataIn)

        outputs = {outp: [] for outp in dOut}
        for wordIndx in range(ITEMS):
            for inp, outp in zip(dIn, dOut):
                # generate register if is not last item
                s = self._sig("item_%d_%s" % (wordIndx, inp._name), inp._dtype)

                if wordIndx <= ITEMS - 1:
                    r = self._reg("reg_" + inp._name + "_%d" % wordIndx, inp._dtype, defVal=0)

                    If(hs & isLastItem,
                       r ** 0
                    ).Elif(vld & itemCntr._eq(wordIndx),
                       r ** inp
                    )

                    If(itemCntr._eq(wordIndx),
                       s ** inp
                    ).Else(
                       s ** r
                    )
                else:  # last item does not need register
                    If(itemCntr._eq(wordIndx),
                       s ** inp
                    ).Else(
                       s ** 0
                    )

                outputs[outp].append(s)

        # dataIn/dataOut hs
        self.getRd(self.dataIn) ** self.getRd(dataOut)
        self.getVld(dataOut) ** (vld & (isLastItem))

        # connect others signals directly
        for inp, outp in zip(self.getData(self.dataIn), self.getData(dataOut)):
            if inp not in dIn:
                outp ** inp

        # connect data signals to utput
        for outp, outItems in outputs.items():
            outp ** Concat(*reversed(outItems))

        # itemCntr next logic
        If(hs,
            If(isLastItem,
                itemCntr ** 0
            ).Else(
                itemCntr ** (itemCntr + 1)
            )
        )

    def downscale(self, IN_DW, OUT_DW):
        if IN_DW % OUT_DW != 0:
            raise NotImplementedError()
        dOut = self.getDataWidthDependent(self.dataOut)
        dataIn = AxiSBuilder(self, self.dataIn).reg().end
        dIn = self.getDataWidthDependent(dataIn)

        ITEMS = IN_DW // OUT_DW
        itemCntr = self._reg("itemCntr", vecT(log2ceil(ITEMS + 1)), defVal=0)

        hs = streamAck([dataIn], [self.dataOut])
        isLastItem = itemCntr._eq(ITEMS - 1)
        strbLastOverride = self.nextAreNotValidLogic(dataIn.strb,
                                                     itemCntr,
                                                     ITEMS,
                                                     OUT_DW)
        if strbLastOverride is not True:
            isLastItem = isLastItem | strbLastOverride

        # connected item selected by itemCntr to output
        for inp, outp in zip(dIn, dOut):
            w = outp._dtype.bit_length()
            Switch(itemCntr)\
            .addCases([
                (wordIndx, outp ** inp[((wordIndx + 1) * w):(w * wordIndx)])
                  for wordIndx in range(ITEMS)
                ])\
            .Default(
               outp ** None
            )

        # connect others signals directly
        for inp, outp in zip(self.getData(dataIn), self.getData(self.dataOut)):
            if inp not in dIn and inp is not dataIn.last:
                outp ** inp

        self.dataOut.last ** (dataIn.last & isLastItem)
        self.getRd(dataIn) ** (self.getRd(self.dataOut) & isLastItem & dataIn.valid)
        self.getVld(self.dataOut) ** self.getVld(dataIn)

        If(hs,
           If(isLastItem,
               itemCntr ** 0
           ).Else(
               itemCntr ** (itemCntr + 1)
           )
        )

    def _impl(self):
        IN_DW = evalParam(self.DATA_WIDTH).val
        OUT_DW = evalParam(self.OUT_DATA_WIDTH).val

        if IN_DW < OUT_DW:  # UPSCALE
            self.upscale(IN_DW, OUT_DW)
        elif IN_DW > OUT_DW:  # DOWNSCALE
            self.downscale(IN_DW, OUT_DW)
        else:  # same
            raise AssertionError("Input and output width are same, this instance is useless")

if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    from hwtLib.amba.axis import AxiStream_withId

    u = AxiS_resizer(AxiStream_withId)
    u.DATA_WIDTH.set(64)
    u.OUT_DATA_WIDTH.set(32)
    print(toRtl(u))
