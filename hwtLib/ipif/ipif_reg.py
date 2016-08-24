from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.interfaces.ipif import IPIF
from hdl_toolkit.interfaces.utils import addClkRstn
"""
        self.bus2ip_addr = s(dtype=vecT(self.ADDR_WIDTH), alternativeNames=["b2i_addr"]) 
        self.bus2ip_data = s(dtype=vecT(self.DATA_WIDTH), alternativeNames=["b2i_data"])
        # byte enable for bus2ip_data
        self.bus2ip_be = s(dtype=vecT(4), alternativeNames=["b2i_be"])
        
        # A High level indicates the transfer request is a user IP read. 
        # A Low level indicates the transfer request is a user IP write.
        self.bus2ip_rnw = s(alternativeNames=["b2i_rnw"])
        
        # chip select
        self.bus2ip_cs = s(alternativeNames=["b2i_cs"])

        self.ip2bus_data = s(dtype=vecT(self.DATA_WIDTH), masterDir=D.IN, alternativeNames=["i2b_data"]) 
        # write ack
        self.ip2bus_wrack = s(masterDir=D.IN, alternativeNames=["i2b_wrack"])
        # read ack
        self.ip2bus_rdack = s(masterDir=D.IN, alternativeNames=["i2b_rdack"])
        self.ip2bus_error = s(masterDir=D.IN, alternativeNames=["i2b_error"])
"""
from hdl_toolkit.hdlObjects.specialValues import DIRECTION
from hdl_toolkit.synthesizer.codeOps import connect, If


class IpifReg(Unit):
    def _config(self):
        IPIF._config(self)
    
    def _declr(self):
        with self._asExtern(), self._paramsShared():
            addClkRstn(self)
            self.dataIn = IPIF()
            self.dataOut = IPIF()
    
    def connectRegistered(self, intfFrom, intfTo):
        r = self._reg(intfFrom._name + "_reg", intfFrom._dtype)
        intfFrom._reg = r
        connect(intfFrom, r)
        connect(r, intfTo)
            
    def _impl(self):
        din = self.dataIn
        dout = self.dataOut
        for i in din._interfaces:
            # exclude bus2ip_cs because it needs special care
            if i is din.bus2ip_cs:
                continue
            if i._masterDir == DIRECTION.OUT:
                _din = i
                _dout = getattr(dout, i._name)
            else:
                _dout = i
                _din = getattr(dout, i._name)
                
            self.connectRegistered(_din, _dout)

        cs = self._reg("bus2ip_cs_reg", defVal=0)
        # now bus2ip_cs has to be set after addr etc are valid
        # but we must not let start another transaction directly after one ended
        If(dout.ip2bus_rdack._reg | dout.ip2bus_wrack._reg,
            connect(0, cs),
            connect(0, dout.bus2ip_cs)
        ).Else(
            connect(din.bus2ip_cs, cs),
            connect(cs, dout.bus2ip_cs)
        )
        

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = IpifReg()

    print(toRtl(u))
    
