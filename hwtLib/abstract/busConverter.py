from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.interfaces.std import BramPort_withoutClk, RegCntrl
from hdl_toolkit.interfaces.utils import log2ceil
from hdl_toolkit.hdlObjects.types.typeCast import toHVal
from hwtLib.abstract.addrSpace import AddrSpaceItem
from hdl_toolkit.synthesizer.param import evalParam

def unpackAddrMap(am):
    try:
        size = am[2]
    except IndexError:
        size = None
    
    # address, name, size
    return am[0], am[1], size
    
    
class BusConverter(Unit):
    def __init__(self, adress_map):
        """
        @param address_map: array of tupes (address, name) or (address, name, size) 
                            where size is in data words
                    
                    for every tuple without size there will be RegCntrl interface
                    for every tuble with size there will be blockram port without clk
        """
        self.ADRESS_MAP = adress_map 
        super().__init__()
    
    def getMinAddr(self):
        return self.ADRESS_MAP[0][0]
    
    def getMaxAddr(self):
        m = self.ADRESS_MAP[-1]
        if len(m) == 2:
            return toHVal(m[0])
        elif len(m) == 3:
            # base + size -1
            return toHVal(m[0]) + (m[2] - 1)
    
    def suggestedAddrWidth(self):
        maxAddr = evalParam(self.getMaxAddr()).val
        return maxAddr.bit_length()
        
    def decorateWithConvertedInterfaces(self):
        assert len(self.ADRESS_MAP) > 0
 
        self._directlyMapped = []
        self._bramPortMapped = []
        self._addrSpace = []
        
        for am in self.ADRESS_MAP:
            addr, name, size = unpackAddrMap(am)
            if size is None:
                size = 1
                p = RegCntrl()
                p._replaceParam("DATA_WIDTH", self.DATA_WIDTH)
                self._directlyMapped.append((addr, p))
            else:
                p = BramPort_withoutClk()
                p._replaceParam("DATA_WIDTH", self.DATA_WIDTH)
                p.ADDR_WIDTH.set(log2ceil(size - 1))
                self._bramPortMapped.append((addr, p, size))

            ai = AddrSpaceItem(addr, name, size)
            self._addrSpace.append(ai)
            p._addrSpaceItem = ai
            
            setattr(self, name, p)
    