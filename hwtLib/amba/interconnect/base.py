from hwt.code import connect, log2ceil
from hwt.synthesizer.unit import Unit
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.handshaked.streamNode import StreamNode
from hwtLib.logic.oneHotToBin import oneHotToBin


def getSizeWidth(maxLen, dataWidth):
    alignBits = log2ceil(dataWidth // 8 - 1)
    lenBits = log2ceil(maxLen) + 1
    return lenBits + alignBits


class AxiInterconnectBase(Unit):
    """
    Abstract class for axi interconnects
    """
    def getDpIntf(self, unit):
        raise NotImplementedError("Implement this function in your implementation")

    def configureFromDrivers(self, drivers, datapump, byInterfaces=False):
        """
        Check configuration of drivers and resolve MAX_LEN and aply it on datapump
        and this interconnect
        """
        if byInterfaces:
            _datapump = datapump.driver

        ID_WIDTH = int(_datapump.ID_WIDTH)
        ADDR_WIDTH = int(_datapump.ADDR_WIDTH)
        DATA_WIDTH = int(_datapump.DATA_WIDTH)
        MAX_LEN = int(_datapump.MAX_LEN)

        for d in drivers:
            if byInterfaces:
                d = self.getDpIntf(d)

            assert ID_WIDTH == int(d.ID_WIDTH)
            assert ADDR_WIDTH == int(d.ADDR_WIDTH)
            assert DATA_WIDTH == int(d.DATA_WIDTH)
            MAX_LEN = max(MAX_LEN, int(d.MAX_LEN))

        if datapump._ctx.synthesised:
            dpMaxLen = int(datapump.MAX_LEN)
            assert dpMaxLen == MAX_LEN, (dpMaxLen, MAX_LEN)
        else:
            datapump.MAX_LEN = MAX_LEN

        self.ID_WIDTH = ID_WIDTH
        self.ADDR_WIDTH = ADDR_WIDTH
        self.DATA_WIDTH = DATA_WIDTH
        self.MAX_LEN = MAX_LEN
        self.MAX_TRANS_OVERLAP = int(datapump.MAX_TRANS_OVERLAP)
        self.DRIVER_CNT = len(drivers)

    def connectDrivers(self, drivers, datapump):
        """
        Connect drivers to datapump using this component
        """
        for i, driver in enumerate(drivers):
            # width of signals should be configured by the widest
            # others drivers can have smaller widths of some signals for example id
            connect(self.getDpIntf(driver), self.drivers[i], fit=True)

        datapump.driver(self.getDpIntf(self))

    def reqHandler(self, dpReq, orderFifoIn):
        # join with roundrobin on requests form drivers and selected index is stored into orderFifo

        # because it is just proxy
        driversReq = list(map(lambda d: d.req, self.drivers))
        b = HsBuilder.join_fair(self, driversReq, exportSelected=True)
        req = b.end
        reqJoin = b.lastComp

        StreamNode(masters=[req],
                   slaves=[dpReq, orderFifoIn]).sync()
        connect(req, dpReq, exclude=[dpReq.vld, dpReq.rd])
        orderFifoIn.data(oneHotToBin(self, reqJoin.selectedOneHot.data))
