from hwt.bitmask import mask
from hwt.code import log2ceil, Switch, If, isPow2
from hwt.hdlObjects.transactionTemplate import TransactionTemplate
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.hdlObjects.types.struct import HStruct
from hwt.interfaces.std import Handshaked
from hwt.interfaces.structIntf import StructIntf
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.param import evalParam
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.base import AxiSCompBase
from hwtLib.handshaked.streamNode import streamSync, streamAck


class AxiS_frameForge(AxiSCompBase):
    """
    Assemble fields into frame on axi stream interface
    """
    def __init__(self, axiSIntfCls, structT):
        """
        :param hsIntfCls: class of interface which should be used as interface of this unit
        :param structT: instance of HStruct used as template for this frame
            if name is None no input port is generated and space is filled with invalid values
            litle-endian encoding,
            supported types of interfaces are: Handshaked, Signal
        """
        if axiSIntfCls is not AxiStream:
            raise NotImplementedError()

        self._structT = structT

        AxiSCompBase.__init__(self, axiSIntfCls)

    @staticmethod
    def _mkFieldIntf(frameTemplateItem):
        p = Handshaked()
        p.DATA_WIDTH.set(frameTemplateItem.dtype.bit_length())
        return p

    def _declr(self):
        addClkRstn(self)
        self.dataOut = self.intfCls()
        self.dataIn = StructIntf(self._structT, self._mkFieldIntf)

    def _impl(self):
        dout = self.dataOut
        tmpl = TransactionTemplate.fromHStruct(self._structT)
        DW = evalParam(self.DATA_WIDTH).val
        _, bitAddrOfEnd, _ = tmpl.discoverTransactionParts(DW)
        maxWordIndex = (bitAddrOfEnd - 1) // DW

        useCounter = maxWordIndex > 0
        if useCounter:
            # multiple word frame
            wordCntr_inversed = self._reg("wordCntr_inversed",
                                          vecT(log2ceil(maxWordIndex + 1), False),
                                          defVal=maxWordIndex)
            wcntrSw = Switch(wordCntr_inversed)

        for i, transactionParts in tmpl.walkFrameWords(skipPadding=False):
            inPorts = []
            wordData = self._sig("word%d" % i, dout.data._dtype)

            for tPart in transactionParts:
                high, low = tPart.getBusWordBitRange()
                if tPart.isPadding:
                    wordData[high:low] ** None
                else:
                    intf = self.dataIn._fieldsToInterfaces[tPart.parent.origin]
                    wordData[high:low] ** intf.data
                    inPorts.append(intf)

            if useCounter:
                if i == maxWordIndex:
                    nextWordIndex = maxWordIndex
                else:
                    nextWordIndex = wordCntr_inversed - 1

            if inPorts:
                # input ready logic
                wordEnConds = {}
                for intf in inPorts:
                    wordEnConds[intf] = dout.ready
                    if useCounter:
                        c = wordEnConds[intf]
                        wordEnConds[intf] = c & wordCntr_inversed._eq(maxWordIndex - i)

                streamSync(masters=inPorts,
                           # slaves=[dout],
                           extraConds=wordEnConds)

            if inPorts:
                ack = streamAck(masters=inPorts)
            else:
                ack = 1

            if useCounter:
                # word cntr next logic
                if ack is 1:
                    _ack = dout.ready
                else:
                    _ack = ack & dout.ready
                a = If(_ack,
                       wordCntr_inversed ** nextWordIndex
                    )
            else:
                a = []

            a.extend(dout.valid ** ack)
            # data out logic
            a.extend(dout.data ** wordData)

            if useCounter:
                wcntrSw.Case(maxWordIndex - i, a)

        # to prevent latches
        if not useCounter:
            pass
        elif not isPow2(maxWordIndex + 1):
            default = wordCntr_inversed ** maxWordIndex
            default.extend(dout.valid ** 0)
            default.extend(dout.data ** None)

            wcntrSw.Default(default)

        if useCounter:
            dout.last ** wordCntr_inversed._eq(0)
        else:
            dout.last ** 1

        dout.strb ** mask(8)


if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    from hwtLib.types.ctypes import uint64_t, uint8_t, uint16_t
    u = AxiS_frameForge(AxiStream,
                        # tuples (type, name) where type has to be instance of Bits type
                        HStruct(
                            (uint64_t, "item0"),
                            (uint64_t, None),  # name = None means field is padding
                            (uint64_t, "item1"),
                            (uint8_t, "item2"), (uint8_t, "item3"), (uint16_t, "item4")
                        )
                        )
    u.DATA_WIDTH.set(64)

    print(toRtl(u))
