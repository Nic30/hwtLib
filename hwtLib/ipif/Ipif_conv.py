from hdl_toolkit.hdlObjects.types.enum import Enum
from hdl_toolkit.hdlObjects.types.typeCast import toHVal
from hdl_toolkit.interfaces.ipif import IPIF
from hdl_toolkit.interfaces.utils import addClkRstn
from hdl_toolkit.synthesizer.codeOps import If, c, FsmBuilder, Switch
from hdl_toolkit.synthesizer.param import evalParam
from hwtLib.abstract.busConverter import BusConverter
from hwtLib.abstract.addrSpace import AddrSpaceItem


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
        
    def _impl(self):
        DW_B = evalParam(self.DATA_WIDTH).val // 8 
        # build read data output mux
        def isMyAddr(addrSig, addr, size):
            return (addrSig >= addr) & (addrSig < (toHVal(addr) + (size * DW_B)))
        
        st_t = Enum('st_t', ['idle', "writeAck", 'readDelay', 'rdData'])
        ipif = self.bus
        addr = ipif.bus2ip_addr
        c(0, ipif.ip2bus_error)
        addrVld = ipif.bus2ip_cs
        
        isInMyAddrSpace = (addr >= self.getMinAddr()) & (addr <= self.getMaxAddr())
        
        st = FsmBuilder(self, st_t)\
        .Trans(st_t.idle,
            (addrVld & isInMyAddrSpace & ipif.bus2ip_rnw, st_t.readDelay),
            (addrVld & isInMyAddrSpace & ~ipif.bus2ip_rnw, st_t.writeAck)
        ).Trans(st_t.writeAck,
            st_t.idle    
        ).Trans(st_t.readDelay,
            st_t.rdData
        ).Default(# Trans(rSt_t.rdData,
            st_t.idle
        ).stateReg
        
        wAck = st._eq(st_t.writeAck)
        c(st._eq(st_t.rdData), ipif.ip2bus_rdack)
        c(wAck, ipif.ip2bus_wrack)
        
        dataToBus = c(None, ipif.ip2bus_data)    
        for ai in reversed(self._bramPortMapped):
            # map addr for bram ports
            _isMyAddr = isMyAddr(addr, ai.addr, ai.size)
            
            a = self._sig("addr_forBram_" + ai.port._name, ipif.bus2ip_addr._dtype)
            c(addr - ai.addr, a)
            
            addrHBit = ai.port.addr._dtype.bit_length()
            if ai.alignOffsetBits:
                bitForAligig = ai.alignOffsetBits
                assert addrHBit + bitForAligig <= evalParam(self.ADDR_WIDTH).val
                c(a[(addrHBit + bitForAligig):bitForAligig], ai.port.addr, fit=True)
            else:
                c(a[addrHBit:], ai.port.addr, fit=True)
                
            c(_isMyAddr, ai.port.en)
            c(_isMyAddr & wAck, ai.port.we)
            
            dataToBus = If(_isMyAddr,
                c(ai.port.dout, ipif.ip2bus_data)
            ).Else(
                dataToBus
            )
            
            c(ipif.bus2ip_data, ai.port.din)


        
        for ai in   self._directlyMapped:
            c(addr._eq(ai.addr) & ~ipif.bus2ip_rnw & wAck, ai.port.dout.vld)
            c(ipif.bus2ip_data, ai.port.dout.data)
        
        _isInBramFlags = []
        Switch(ipif.bus2ip_addr)\
        .addCases(
                [(ai.addr, c(ai.port.din, ipif.ip2bus_data)) 
                 for ai in   self._directlyMapped]
        ).Default(
            dataToBus
        )
        

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    #u = IpifConverter([(i * 4 , "data%d" % i) for i in range(2)] + 
    #                  [(3 * 4, "bramMapped", 32)])
    #
    u = IpifConverter([(i * 4 , "data%d" % i) for i in range(2)] + 
                      [AddrSpaceItem(3 * 4, "bramMapped", 32, 2)])
    
    print(toRtl(u))
    
