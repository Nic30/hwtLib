from hwt.code import log2ceil, connect
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam
from hwtLib.axi.axiDatapumpIntf import AxiRDatapumpIntf
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import streamSync


class RStrictOrderInterconnect(Unit):
    """
    Strict order interconnect for AxiRDatapumpIntf
    ensures that response on request is delivered to driver which asked for it while transactions can overlap
    """
    def _config(self):
        self.DRIVER_CNT = Param(2)
        self.MAX_OVERLAP = Param(16)
        AxiRDatapumpIntf._config(self)
    
    def configureFromDrivers(self, drivers, datapump):
        """
        Check configuration of drivers and resolve MAX_LEN and aply it on datapump
        and this interconnect
        """
        e = lambda p: evalParam(p).val
        ID_WIDTH = e(datapump.ID_WIDTH)
        ADDR_WIDTH = e(datapump.ADDR_WIDTH)
        DATA_WIDTH = e(datapump.DATA_WIDTH)
        MAX_LEN = e(datapump.MAX_LEN)
        for d in drivers:
            assert ID_WIDTH == e(d.ID_WIDTH)
            assert ADDR_WIDTH == e(d.ADDR_WIDTH)
            assert DATA_WIDTH == e(d.DATA_WIDTH)
            MAX_LEN = max(MAX_LEN, e(d.MAX_LEN))
        
        datapump.MAX_LEN.set(MAX_LEN)

        self.ID_WIDTH.set(ID_WIDTH)
        self.ADDR_WIDTH.set(ADDR_WIDTH)
        self.DATA_WIDTH.set(DATA_WIDTH)
        self.MAX_LEN.set(MAX_LEN)
        self.MAX_OVERLAP.set(e(datapump.MAX_OVERLAP))
    
    def connectAll(self, drivers, datapump):
        raise NotImplementedError()

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.drivers = AxiRDatapumpIntf(multipliedBy=self.DRIVER_CNT)
            self.rDatapump = AxiRDatapumpIntf()
        
        self.DRIVER_INDEX_WIDTH = log2ceil(self.DRIVER_CNT).val
        
        f = self.orderInfoFifo = HandshakedFifo(Handshaked)
        f.DEPTH.set(self.MAX_OVERLAP)
        f.DATA_WIDTH.set(self.DRIVER_INDEX_WIDTH) 
    
    def indexOfActiveReq(self):
        raise NotImplementedError()
    
    def _impl(self):
        propagateClkRstn(self)
        fifoIn = self.orderInfoFifo.dataIn
        fifoOut = self.orderInfoFifo.dataOut
        r = self.rDatapump.r
        
        dpReq = self.rDatapump.req

        req = HsBuilder.join(self, map(lambda d: d.req, self.drivers)).end
        streamSync(masters=[req],
                   slaves=[dpReq,
                           fifoIn])
        connect(req, dpReq, exclude=[dpReq.vld, dpReq.rd])
        fifoIn.data ** self.indexOfActiveReq()
        fifoOut.rd ** (r.valid & r.last & selectedDriverReady)
        
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = RStrictOrderInterconnect()
    print(toRtl(u))
