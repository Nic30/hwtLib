from hdl_toolkit.hdlObjects.types.enum import Enum
from hdl_toolkit.hdlObjects.types.typeCast import toHVal
from hdl_toolkit.interfaces.utils import addClkRstn, log2ceil
from hdl_toolkit.synthesizer.codeOps import If, c, FsmBuilder, Switch
from hdl_toolkit.synthesizer.param import evalParam
from hwtLib.abstract.busConverter import BusConverter
from hdl_toolkit.interfaces.ipif import IPIF

class IpifConverter(BusConverter):
    """
    IPIF converter generator
    byte enable and register clock enable signals are ignored
    """
    def _config(self):
        IPIF._config(self)

    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            
            with self._paramsShared():
                self.bus = IPIF()
                
            self.decorateWithConvertedInterfaces()

    def getMinAddr(self):
        return self.ADRESS_MAP[0][0]
    
    def getMaxAddr(self):
        m = self.ADRESS_MAP[-1]
        if len(m) == 2:
            return m[0]
        elif len(m) == 3:
            # base + size -1
            return toHVal(m[0]) + (m[2] - 1)
    
    
    def _impl(self):
        DW_B = evalParam(self.DATA_WIDTH).val // 8 
        bitForAligig = log2ceil(self.DATA_WIDTH // 8 - 1).val
        # build read data output mux
        def isMyAddr(addrSig, addr, size):
            return (addrSig >= addr) & (addrSig < (toHVal(addr) + (size * DW_B)))
        
        st_t = Enum('st_t', ['idle', 'readDelay', 'rdData'])
        ipif = self.bus
        addr = ipif.bus2ip_addr
        c(0, ipif.ip2bus_error)
        addrVld = ipif.bus2ip_cs
        
        isInMyAddrSpace = (addr >= self.getMinAddr()) & (addr <= self.getMaxAddr())
        
        st = FsmBuilder(self, st_t)\
        .Trans(st_t.idle,
            (addrVld & ipif.bus2ip_rnw & isInMyAddrSpace, st_t.readDelay),
        ).Trans(st_t.readDelay,
            st_t.rdData
        ).Default(# Trans(rSt_t.rdData,
            st_t.idle
        ).stateReg
        
        c(st._eq(st_t.rdData), ipif.ip2bus_rdack)
        c(isInMyAddrSpace & ~ipif.bus2ip_rnw, ipif.ip2bus_wrack)
        
        dataToBus = c(None, ipif.ip2bus_data)    
        for _addr, port, size in reversed(self._bramPortMapped):
            # map addr for bram ports
            _isMyAddr = isMyAddr(addr, _addr, size)
            
            a = self._sig("addr_forBram_" + port._name, ipif.bus2ip_addr._dtype)
            c(addr - _addr, a)
            
            addrHBit = port.addr._dtype.bit_length() 
            assert addrHBit + bitForAligig <= evalParam(self.ADDR_WIDTH).val
            
            c(a[(addrHBit + bitForAligig):bitForAligig], port.addr, fit=True)
            c(_isMyAddr, port.en)
            c(_isMyAddr & ~ipif.bus2ip_rnw, port.we)
            
            dataToBus = If(_isMyAddr,
                c(port.dout, ipif.ip2bus_data)
            ).Else(
                dataToBus
            )
            
            c(ipif.bus2ip_data, port.din)


        
        for _addr, d in   self._directlyMapped:
            c(addr._eq(_addr) & ~ipif.bus2ip_rnw, d.dout.vld)
            c(ipif.bus2ip_data, d.dout.data)
        
        _isInBramFlags = []
        Switch(ipif.bus2ip_addr)\
        .addCases(
                [(_addr, c(d.din, ipif.ip2bus_data)) 
                 for _addr, d in   self._directlyMapped]
        ).Default(
            dataToBus
        )
        

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = IpifConverter([(i * 4 , "data%d" % i) for i in range(2)] + 
                      [(3 * 4, "bramMapped", 32)])
    
    print(toRtl(u))
    
