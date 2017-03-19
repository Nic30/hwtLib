#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwtLib.structManipulators.structReader import StructReader
from hwt.interfaces.std import Handshaked, HandshakeSync
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwtLib.structManipulators.structUtils import StructBusBurstInfo
from hwt.synthesizer.param import evalParam
from hwtLib.amba.axiDatapumpIntf import AxiWDatapumpIntf
from hwt.code import ForEach, log2ceil, If
from hwtLib.handshaked.streamNode import streamSync
from hwt.hdlObjects.typeShortcuts import vecT
from hwtLib.amba.axis_comp.frameForge import AxiSFrameForge
from hwtLib.amba.axis import AxiStream
from hwtLib.handshaked.fifo import HandshakedFifo


class StructWriter(StructReader):

    def _createInterfaceForField(self, fInfo):
        i = Handshaked()
        i.DATA_WIDTH.set(fInfo.type.bit_length())
        fInfo.interface = i
        return i

    def _declr(self):
        addClkRstn(self)

        structInfo = self._declareFieldInterfaces()
        self._busBurstInfo = StructBusBurstInfo.packFieldInfosToBusBurst(
                                    structInfo,
                                    evalParam(self.MAX_DUMMY_WORDS).val,
                                    evalParam(self.DATA_WIDTH).val // 8)

        self.set = Handshaked()  # data signal is addr of structure to write
        self.set._replaceParam("DATA_WIDTH", self.ADDR_WIDTH)
        # write ack from slave
        self.writeAck = HandshakeSync()

        with self._paramsShared():
            # interface for communication with datapump
            self.wDatapump = AxiWDatapumpIntf()
            self.wDatapump.MAX_LEN.set(StructBusBurstInfo.sumOfWords(self._busBurstInfo))

        self.frameAssember = []
        for burstInfo in self._busBurstInfo:
            frameTemplate = [(f.type, f.name) for f in burstInfo.fieldInfos]
            f = AxiSFrameForge(AxiStream, frameTemplate)
            self.frameAssember.append(f)
        self._registerArray(self.frameAssember, "frameAssember")

    def _impl(self):
        propagateClkRstn(self)

        req = self.wDatapump.req
        w = self.wDatapump.w
        ack = self.wDatapump.ack

        req.id ** self.ID
        req.rem ** 0

        if len(self._busBurstInfo) > 1:
            frameIndx = self._reg("frameIndx",
                                  vecT(log2ceil(len(self._busBurstInfo)), False),
                                  defVal=0)
            ackPropageteInfo = HandshakedFifo(Handshaked)
            ackPropageteInfo.DATA_WIDTH.set(1)
            self.ackPropageteInfo = ackPropageteInfo
        else:
            frameIndx = None

        for burstInfo, frameAssembler in zip(self._busBurstInfo, self.frameAssember):
            for fieldInfo in burstInfo.fieldInfos:
                if frameIndx is None:
                    # we have only single frame
                    intf = getattr(frameAssembler, fieldInfo.name)
                    intf ** fieldInfo.interface


        def f(burst):
            return [req.addr ** (self.get.data + burst.addrOffset),
                    req.len ** (burst.wordCnt() - 1),
                    ]
        ForEach(self, self._busBurstInfo, f, ack=req.rd)

        streamSync(masters=[self.set], slaves=[req])


if __name__ == "__main__":
    from hwtLib.types.ctypes import uint16_t, uint32_t, uint64_t
    from hwt.synthesizer.shortcuts import toRtl

    s = [
        (uint64_t, "item0"),  # tuples (type, name) where type has to be instance of Bits type
        (uint64_t, None),  # name = None means this field will be ignored
        (uint64_t, "item1"),
        (uint64_t, None),
        (uint16_t, "item2"),
        (uint16_t, "item3"),
        (uint32_t, "item4"),

        (uint32_t, None),
        (uint64_t, "item5"),  # this word is split on two bus words
        (uint32_t, None),

        (uint64_t, None),
        (uint64_t, None),
        (uint64_t, None),
        (uint64_t, "item6"),
        (uint64_t, "item7"),
        ]

    u = StructWriter(s)
    print(toRtl(u))