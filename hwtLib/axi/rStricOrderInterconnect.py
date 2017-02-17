from hwt.code import log2ceil, connect, Or
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam
from hwtLib.axi.axiDatapumpIntf import AxiRDatapumpIntf
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import streamSync
from hwtLib.logic.oneHotToBin import oneHotToBin
from hwt.serializer.constants import SERI_MODE


class RStrictOrderInterconnect(Unit):
    """
    Strict order interconnect for AxiRDatapumpIntf
    ensures that response on request is delivered to driver which asked for it while transactions can overlap
    """
    _serializerMode = SERI_MODE.PARAMS_UNIQ
    
    def _config(self):
        self.DRIVER_CNT = Param(2)
        self.MAX_TRANS_OVERLAP = Param(16)
        AxiRDatapumpIntf._config(self)
    
    def configureFromDrivers(self, drivers, datapump, byInterfaces=False):
        """
        Check configuration of drivers and resolve MAX_LEN and aply it on datapump
        and this interconnect
        """
        if byInterfaces:
            _datapump = datapump.driver
            
        e = lambda p: evalParam(p).val
        ID_WIDTH = e(_datapump.ID_WIDTH)
        ADDR_WIDTH = e(_datapump.ADDR_WIDTH)
        DATA_WIDTH = e(_datapump.DATA_WIDTH)
        MAX_LEN = e(_datapump.MAX_LEN)
        
        for d in drivers:
            if byInterfaces:
                d = d.rDatapump
            
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
            connect(driver.rDatapump, self.drivers[i], fit=True) 
        
        datapump.driver ** self.rDatapump

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.drivers = AxiRDatapumpIntf(multipliedBy=self.DRIVER_CNT)
            self.rDatapump = AxiRDatapumpIntf()
        
        self.DRIVER_INDEX_WIDTH = log2ceil(self.DRIVER_CNT).val
        
        f = self.orderInfoFifo = HandshakedFifo(Handshaked)
        f.DEPTH.set(self.MAX_TRANS_OVERLAP)
        f.DATA_WIDTH.set(self.DRIVER_INDEX_WIDTH) 
        
    def _impl(self):
        propagateClkRstn(self)
        fifoIn = self.orderInfoFifo.dataIn
        fifoOut = self.orderInfoFifo.dataOut
        r = self.rDatapump.r
        
        dpReq = self.rDatapump.req

        req = HsBuilder.join(self, map(lambda d: d.req,
                                       self.drivers)).end
        streamSync(masters=[req],
                   slaves=[dpReq, fifoIn])
        connect(req, dpReq, exclude=[dpReq.vld, dpReq.rd])
        fifoIn.data ** oneHotToBin(self, map(lambda d: d.req.vld,
                                             self.drivers))
        
        driversR = list(map(lambda d: d.r,
                            self.drivers))

        selectedDriverReady = self._sig("selectedDriverReady")
        selectedDriverReady ** Or(*map(lambda d : fifoOut.data._eq(d[0]) & d[1].ready,
                                       enumerate(driversR))
                                       )
        
        # extra enable signals based on selected driver from orderInfoFifo
        extraHsEnableConds = {
                              fifoOut : [r.last & selectedDriverReady] # on end of frame pop new item
                             }
        for i, d in enumerate(driversR):
            extraHsEnableConds[d] = [fifoOut.data._eq(i)]
            connect(r, d, exclude=[d.valid, d.ready])
        
        streamSync(masters=[r, fifoOut],
                   slaves=driversR,
                   extraConds=extraHsEnableConds)
        
        
        
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = RStrictOrderInterconnect()
    print(toRtl(u))
