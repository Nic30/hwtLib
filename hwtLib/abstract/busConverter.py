from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.interfaces.std import BramPort_withoutClk, RegCntrl
from hwt.interfaces.utils import log2ceil
from hwt.hdlObjects.types.typeCast import toHVal
from hwtLib.abstract.addrSpace import AddrSpaceItem
from hwt.synthesizer.param import evalParam

def unpackAddrMap(am):
    if isinstance(am, AddrSpaceItem):
        return am
    try:
        size = am[2]
    except IndexError:
        size = None
    
    # address, name, size
    return AddrSpaceItem(am[0], am[1], size)
    
class BusConverter(Unit):
    def __init__(self, adress_map):
        """
        @param address_map: array of tupes (address, name) or (address, name, size) 
                            where size is in data words or AddrSpaceItem objects
                    
                    for every tuple without size there will be RegCntrl interface
                    for every tuble with size there will be blockram port without clk
        """
        self.ADRESS_MAP = list(sorted(map(unpackAddrMap, adress_map), key=lambda x: x.addr))
        super().__init__()
    
    def getMinAddr(self):
        return self.ADRESS_MAP[0].addr
    
    def getMaxAddr(self):
        m = self.ADRESS_MAP[-1]
        if m.size is not None:
            if m.alignOffsetBits:
                size = evalParam(m.size).val << m.alignOffsetBits;
            else:
                size = m.size
                
            return toHVal(m.addr) + (size - 1)
        else:
            return toHVal(m.addr)
    
    def suggestedAddrWidth(self):
        maxAddr = evalParam(self.getMaxAddr()).val
        return maxAddr.bit_length()
        
    def decorateWithConvertedInterfaces(self):
        assert len(self.ADRESS_MAP) > 0
 
        self._directlyMapped = []
        self._bramPortMapped = []
        self._addrSpace = []
        
        for am in self.ADRESS_MAP:
            addrItem = unpackAddrMap(am)
            if addrItem.size is None:
                addrItem.size = 1
                p = RegCntrl()
                p._replaceParam("DATA_WIDTH", self.DATA_WIDTH)
                self._directlyMapped.append(addrItem)
            else:
                p = BramPort_withoutClk()
                p._replaceParam("DATA_WIDTH", self.DATA_WIDTH)
                p.ADDR_WIDTH.set(log2ceil(addrItem.size - 1))
                self._bramPortMapped.append(addrItem)

            self._addrSpace.append(addrItem)
            addrItem.port = p
            p._addrSpaceItem = addrItem
            
            setattr(self, addrItem.name, p)
    
