#from hdl_toolkit.intfLvl import Param
#from hdl_toolkit.synthetisator.codeOps import And, c
#from hdl_toolkit.interfaces.std import Handshaked
#from hdl_toolkit.interfaces.utils import addClkRstn
#from hwtLib.handshaked.compBase import HandshakedCompBase
#
#class HandshakedRegisteredFork(HandshakedCompBase):
#    """
#    Clone input stream to n identical output streams
#    
#    vld is propagated from dataIn to registers for all data out interfaces
#    all of slaves have to take a data before new vld flag can come from dataIn
#    """
#    def _config(self):
#        self.OUTPUTS = Param(2)
#        super()._config()
#        
#    def _declr(self):
#        with self._asExtern(), self._paramsShared():
#            addClkRstn(self)
#            self.dataIn = self.intfCls()
#            self.dataOut = self.intfCls(multipliedBy=self.OUTPUTS)
#
#    def slaveRegHandler(self):
#
#    def _impl(self):
#        """
#        pseudocode:
#            in.rd = all(out.rd)
#            for out in dataOut:
#                out.vld = waitForMe or (not others(waitForMe) and in.vld)
#                waitForMe =   
#            
#            1) wait for vld from master
#               - directly propagate vld
#               - if slave was not ready set waitForMe flag
#                
#            
#        
#        
#        """
#        
#        
#        rd = self.getRd
#        vld = self.getVld
#        data = self.getData
#        
#        for io in self.dataOut:
#            for i, o in zip(data(self.dataIn), data(io)):
#                c(i, o)
#        
#        outRd = And(*[rd(i) for i in self.dataOut])
#        c(outRd, rd(self.dataIn)) 
#
#        for o in self.dataOut:
#            # everyone else is ready and input is valid
#            deps = [vld(self.dataIn)]
#            for otherO in self.dataOut:
#                if otherO is o:
#                    continue
#                deps.append(rd(otherO))
#            _vld = And(*deps)
#            
#            c(_vld, vld(o))  
#        
#        
#if __name__ == "__main__":
#    from hdl_toolkit.synthetisator.shortcuts import toRtl
#    u = HandshakedRegisteredFork(Handshaked)
#    print(toRtl(u))
#