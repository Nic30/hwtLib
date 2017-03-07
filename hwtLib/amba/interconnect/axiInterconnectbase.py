from hwt.code import connect, log2ceil
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import evalParam
from hwtLib.handshaked.joinFair import HsJoinFairShare
from hwtLib.handshaked.streamNode import streamSync
from hwtLib.logic.oneHotToBin import oneHotToBin


def getSizeWidth(maxLen, dataWidth):
    alignBits = log2ceil(dataWidth // 8 - 1).val
    lenBits = log2ceil(maxLen).val
    return lenBits + alignBits

class AxiInterconnectBase(Unit):
    def getDpIntf(self, unit):
        raise NotImplementedError("Implement this function in your implementation")

    def configureFromDrivers(self, drivers, datapump, byInterfaces=False):
        """
        Check configuration of drivers and resolve MAX_LEN and aply it on datapump
        and this interconnect
        """
        def e(p):
            return evalParam(p).val

        if byInterfaces:
            _datapump = datapump.driver

        ID_WIDTH = e(_datapump.ID_WIDTH)
        ADDR_WIDTH = e(_datapump.ADDR_WIDTH)
        DATA_WIDTH = e(_datapump.DATA_WIDTH)
        MAX_LEN = e(_datapump.MAX_LEN)

        for d in drivers:
            if byInterfaces:
                d = self.getDpIntf(d)

            assert ID_WIDTH == e(d.ID_WIDTH)
            assert ADDR_WIDTH == e(d.ADDR_WIDTH)
            assert DATA_WIDTH == e(d.DATA_WIDTH)
            MAX_LEN = max(MAX_LEN, e(d.MAX_LEN))

        datapump.MAX_LEN.set(MAX_LEN)

        self.ID_WIDTH.set(ID_WIDTH)
        self.ADDR_WIDTH.set(ADDR_WIDTH)
        self.DATA_WIDTH.set(DATA_WIDTH)
        self.MAX_LEN.set(MAX_LEN)
        self.MAX_TRANS_OVERLAP.set(e(datapump.MAX_TRANS_OVERLAP))
        self.DRIVER_CNT.set(len(drivers))

    def connectDrivers(self, drivers, datapump):
        """
        Connect drivers to datapump using this component
        """
        for i, driver in enumerate(drivers):
            # width of signals should be configured by the widest
            # others drivers can have smaller widths of some signals for example id
            connect(self.getDpIntf(driver), self.drivers[i], fit=True)

        datapump.driver ** self.getDpIntf(self)

    def reqHandler(self, dpReq, orderFifoIn):
        # join with roundrobin on requests form drivers and selected index is stored into orderFifo
        joinTmpl = self.drivers[0].req
        reqJoin = HsJoinFairShare(joinTmpl.__class__)
        reqJoin._updateParamsFrom(joinTmpl)
        reqJoin.INPUTS.set(self.DRIVER_CNT)
        reqJoin.EXPORT_SELECTED.set(True)

        self.reqJoin = reqJoin

        reqJoin.clk ** self.clk
        reqJoin.rst_n ** self.rst_n
        for i, d in enumerate(self.drivers):
            reqJoin.dataIn[i] ** d.req

        req = reqJoin.dataOut
        streamSync(masters=[req],
                   slaves=[dpReq, orderFifoIn])
        connect(req, dpReq, exclude=[dpReq.vld, dpReq.rd])
        orderFifoIn.data ** oneHotToBin(self, reqJoin.selectedOneHot.data)