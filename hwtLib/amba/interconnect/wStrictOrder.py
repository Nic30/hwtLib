from hwt.code import log2ceil, connect, Or, Switch
from hwt.interfaces.std import Handshaked
from hwt.interfaces.utils import addClkRstn, propagateClkRstn
from hwt.serializer.constants import SERI_MODE
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param, evalParam
from hwtLib.amba.axiDatapumpIntf import AxiWDatapumpIntf
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.handshaked.fifo import HandshakedFifo
from hwtLib.handshaked.streamNode import streamSync
from hwtLib.logic.oneHotToBin import oneHotToBin


class WStrictOrderInterconnect(Unit):
    """
    Strict order interconnect for AxiWDatapumpIntf
    ensures that response on request is delivered to driver which asked for it while transactions can overlap
    """
    _serializerMode = SERI_MODE.PARAMS_UNIQ
    
    def _config(self):
        self.DRIVER_CNT = Param(2)
        self.MAX_TRANS_OVERLAP = Param(16)
        AxiWDatapumpIntf._config(self)
    
    def configureFromDrivers(self, drivers, datapump, byInterfaces=False):
        """
        Check configuration of drivers and resolve MAX_LEN and aply it on datapump
        and this interconnect
        """
        e = lambda p: evalParam(p).val
        
        if byInterfaces:
            _datapump = datapump.driver
        
        ID_WIDTH = e(_datapump.ID_WIDTH)
        ADDR_WIDTH = e(_datapump.ADDR_WIDTH)
        DATA_WIDTH = e(_datapump.DATA_WIDTH)
        MAX_LEN = e(_datapump.MAX_LEN)
        
        for d in drivers:
            if byInterfaces:
                d = d.wDatapump
                
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
            connect(driver.wDatapump, self.drivers[i], fit=True) 
        
        datapump.driver ** self.wDatapump

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.drivers = AxiWDatapumpIntf(multipliedBy=self.DRIVER_CNT)
            self.wDatapump = AxiWDatapumpIntf()
        
        self.DRIVER_INDEX_WIDTH = log2ceil(self.DRIVER_CNT).val
        
        fW = self.orderInfoFifoW = HandshakedFifo(Handshaked)
        fAck = self.orderInfoFifoAck = HandshakedFifo(Handshaked)
        for f in [fW, fAck]:
            f.DEPTH.set(self.MAX_TRANS_OVERLAP)
            f.DATA_WIDTH.set(self.DRIVER_INDEX_WIDTH) 
    
    def reqHandler(self):
        fWIn = self.orderInfoFifoW.dataIn
        dpReq = self.wDatapump.req

        req = HsBuilder.join(self, map(lambda d: d.req,
                                       self.drivers)).end
        streamSync(masters=[req],
                   slaves=[dpReq, fWIn])
        connect(req, dpReq, exclude=[dpReq.vld, dpReq.rd])
        fWIn.data ** oneHotToBin(self, map(lambda d: d.req.vld,
                                             self.drivers))
    def wHandler(self):
        w = self.wDatapump.w
        fWOut = self.orderInfoFifoW.dataOut
        fAckIn = self.orderInfoFifoAck.dataIn
        
        driversW = list(map(lambda d: d.w,
                            self.drivers))

        selectedDriverVld = self._sig("selectedDriverWVld")
        selectedDriverVld ** Or(*map(lambda d : fWOut.data._eq(d[0]) & d[1].valid,
                                       enumerate(driversW))
                                       )
        selectedDriverLast = self._sig("selectedDriverLast")
        selectedDriverLast ** Or(*map(lambda d : fWOut.data._eq(d[0]) & d[1].last,
                                       enumerate(driversW))
                                       )
        
        Switch(fWOut.data).addCases(
            [(i, connect(d, w, exclude=[d.valid, d.ready]))
               for i, d in enumerate(driversW)]
        
        ).Default(
            w.data ** None,
            w.strb ** None,
            w.last ** None
        )

        fAckIn.data ** fWOut.data
        
        # handshake logic
        fWOut.rd ** (selectedDriverVld & selectedDriverLast & w.ready & fAckIn.rd)
        for i, d in enumerate(driversW):
            d.ready ** (fWOut.data._eq(i) & w.ready & fWOut.vld & fAckIn.rd)
        w.valid ** (selectedDriverVld & fWOut.vld & fAckIn.rd)
        fAckIn.vld ** (selectedDriverVld & selectedDriverLast & w.ready & fWOut.vld)

    def ackHandler(self):
        ack = self.wDatapump.ack
        fAckOut = self.orderInfoFifoAck.dataOut
        driversAck = list(map(lambda d: d.ack,
                            self.drivers))

        selectedDriverAckReady = self._sig("selectedDriverAckReady")
        selectedDriverAckReady ** Or(*map(lambda d : fAckOut.data._eq(d[0]) & d[1].rd,
                                       enumerate(driversAck))
                                       )
        
        # extra enable signals based on selected driver from orderInfoFifo
        extraHsEnableConds = {
                              fAckOut : [selectedDriverAckReady]  # on end of frame pop new item
                             }
        for i, d in enumerate(driversAck):
            extraHsEnableConds[d] = [fAckOut.data._eq(i)]
            connect(ack, d, exclude=[d.vld, d.rd])
        
        streamSync(masters=[ack, fAckOut],
                   slaves=driversAck,
                   extraConds=extraHsEnableConds)  
        
        
    def _impl(self):
        propagateClkRstn(self)
        self.reqHandler()
        self.wHandler()
        self.ackHandler()

        
if __name__ == "__main__":
    from hwt.synthesizer.shortcuts import toRtl
    u = WStrictOrderInterconnect()
    print(toRtl(u))
