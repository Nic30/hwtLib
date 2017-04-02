#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.code import ForEach, connect
from hwt.hdlObjects.types.struct import HStruct
from hwt.hdlObjects.types.structUtils import StructBusBurstInfo
from hwt.interfaces.std import Handshaked, Signal
from hwt.interfaces.utils import propagateClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import evalParam, Param
from hwtLib.amba.axiDatapumpIntf import AxiRDatapumpIntf
from hwtLib.amba.axis import AxiStream_withoutSTRB
from hwtLib.amba.axis_comp.frameParser import AxiS_frameParser
from hwtLib.handshaked.streamNode import streamAck


class StructReader(AxiS_frameParser):
    """
    This unit downloads required structure fields over rDatapump interface from address
    specified by get interface
    MAX_DUMMY_WORDS specifies maximum dummy bus words between fields
    if there is more of ignored space transaction will be split to
    :attention: interfaces of field will not send data in same time
    """
    def __init__(self, structT):
        """
        :param structT: instance of HStruct which specifies data format to download
        :attention: interfaces for each field in struct will be dynamically created
        :attention: structT can not contain fields with variable size like HStream
        """
        Unit.__init__(self)
        assert isinstance(structT, HStruct)
        self._structT = structT

    def _config(self):
        self.ID = Param(0)
        self.MAX_DUMMY_WORDS = Param(1)
        AxiRDatapumpIntf._config(self)
        # if this is true field interfaces will be of type VldSynced
        # and single ready signal will be used for all
        # else every interface will be instance of Handshaked and it will
        # have it's own ready(rd) signal
        self.SHARED_READY = Param(False)

    def _declr(self):
        AxiS_frameParser._declr(self, declareInput=False)

        self.get = Handshaked()  # data signal is addr of structure to download
        self.get._replaceParam("DATA_WIDTH", self.ADDR_WIDTH)

        with self._paramsShared():
            # interface for communication with datapump
            self.rDatapump = AxiRDatapumpIntf()
            self.rDatapump.MAX_LEN.set(StructBusBurstInfo.sumOfWords(self._busBurstInfo))
            # [TODO] do not use self._structT (bursts can be formated to something else)
            self.parser = AxiS_frameParser(AxiStream_withoutSTRB, self._structT)
        if evalParam(self.SHARED_READY).val:
            self.ready = Signal()

    def _impl(self):
        propagateClkRstn(self)
        req = self.rDatapump.req

        req.id ** self.ID
        req.rem ** 0

        def f(burst, indx):
            s = [req.addr ** (self.get.data + burst.addrOffset),
                 req.len ** (burst.wordCnt() - 1),
                 req.vld ** self.get.vld
                 ]
            if indx == len(self._busBurstInfo) - 1:
                s.append(self.get.rd ** req.rd)
            else:
                s.append(self.get.rd ** 0)

            ack = streamAck(masters=[self.get], slaves=[self.rDatapump.req])
            return s, ack

        ForEach(self, self._busBurstInfo, f)

        r = self.rDatapump.r
        connect(r, self.parser.dataIn, exclude=[r.id, r.strb])

        for burst in self._busBurstInfo:
            for fieldInfo in burst.fieldInfos:
                myIntf = getattr(self, fieldInfo.name)
                parserIntf = getattr(self.parser, fieldInfo.name)
                myIntf ** parserIntf


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

    u = StructReader(s)
    print(toRtl(u))
