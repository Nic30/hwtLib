#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import ForEach
from hwt.interfaces.std import Handshaked, HandshakeSync
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.param import evalParam, Param
from hwtLib.amba.axiDatapumpIntf import AxiWDatapumpIntf
from hwtLib.amba.axis import AxiStream
from hwtLib.amba.axis_comp.builder import AxiSBuilder
from hwtLib.amba.axis_comp.frameForge import AxiS_frameForge
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import streamSync, streamAck
from hwtLib.structManipulators.structReader import StructReader
from hwtLib.structManipulators.structUtils import StructBusBurstInfo
from hwt.hdlObjects.types.struct import HStruct


class StructWriter(StructReader):
    """
    Write struct specified in constructor over wDatapump interface on address
    specified over set interface
    """
    def _config(self):
        StructReader._config(self)
        self.MAX_OVERLAP = Param(2)

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
            f = AxiS_frameForge(AxiStream, HStruct(*frameTemplate))
            self.frameAssember.append(f)
        self._registerArray("frameAssember", self.frameAssember)

    def _impl(self):
        propagateClkRstn(self)

        req = self.wDatapump.req
        w = self.wDatapump.w
        ack = self.wDatapump.ack

        req.id ** self.ID
        req.rem ** 0

        if len(self._busBurstInfo) > 1:
            # multi frame
            ackPropageteInfo = HandshakedFifo(Handshaked)
            ackPropageteInfo.DATA_WIDTH.set(1)
            ackPropageteInfo.DEPTH.set(self.MAX_OVERLAP)
            self.ackPropageteInfo = ackPropageteInfo
            ackPropageteInfo.clk ** self.clk
            ackPropageteInfo.rst_n ** self.rst_n

            def propagateRequests(burst, indx):
                ack = streamAck(slaves=[req, ackPropageteInfo.dataIn])
                statements = [req.addr ** (self.set.data + burst.addrOffset),
                              req.len ** (burst.wordCnt() - 1),
                              ackPropageteInfo.dataIn.data ** int(indx != 0),
                              ]\
                              + streamSync(slaves=[req, ackPropageteInfo.dataIn],
                                           extraConds={req: self.set.vld,
                                                       ackPropageteInfo.dataIn: self.set.vld})

                isLast = indx == len(self._busBurstInfo) - 1
                if isLast:
                    statements.append(self.set.rd ** ack)
                else:
                    statements.append(self.set.rd ** 0)

                return statements, ack & self.set.vld

            ForEach(self, self._busBurstInfo, propagateRequests)

            # connect write channel
            fa = self.frameAssember
            w ** AxiSBuilder(self, fa[0].dataOut)\
                            .extend(map(lambda a: a.dataOut, fa[1:]))\
                            .end

            # propagate ack
            streamSync(masters=[ack, ackPropageteInfo.dataOut],
                       slaves=[self.writeAck],
                       skipWhen={
                                 self.writeAck: ackPropageteInfo.dataOut.data._eq(0)
                                })
        else:
            # single frame
            fa = self.frameAssember[0]

            def propagateRequests(burst):
                ack = streamAck(masters=[self.set],
                                slaves=[req])
                return [req.addr ** (self.set.data + burst.addrOffset),
                        req.len ** (burst.wordCnt() - 1),
                        ], ack
            ForEach(self, self._busBurstInfo, propagateRequests)

            streamSync(masters=[self.set], slaves=[req])

            w ** fa.dataOut

            # propagate ack
            streamSync(masters=[ack],
                       slaves=[self.writeAck])

        # connect fields to assembers by its name
        for burstInfo, frameAssembler in zip(self._busBurstInfo, self.frameAssember):
            for fieldInfo in burstInfo.fieldInfos:
                intf = getattr(frameAssembler, fieldInfo.name)
                intf ** fieldInfo.interface


if __name__ == "__main__":
    from hwtLib.types.ctypes import uint16_t, uint32_t, uint64_t
    from hwt.synthesizer.shortcuts import toRtl

    s = HStruct(
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
        )

    u = StructWriter(s)
    print(toRtl(u))
