from hdl_toolkit.bitmask import Bitmask
import pprint


class AddrSpaceItem(object):
    def __init__(self, addr, name, size=1):
        self.name = name
        self.addr = addr
        self.size = size
        self.children = {}
    

    def assertNoOverlap(self, nextItem):
        left0 = self.addr + self.size
        right1 = nextItem.addr
        assert left0 <= right1, (self, nextItem)
         
    @staticmethod
    def checkOverlapping(addrSpace):
        """
        @param addrSpace: sorted list of AddrSpaceItems
        """
        last = None
        for item in addrSpace:
            if last is None:
                pass
            else:
                last.assertNoOverlap(item)
                
            last = item
    
    def getMyAddrPrefix(self):
        """
        @return: None if base addr is not aligned to size and prefix can not be used
                 tuple (prefix, subAddrBits) if can be mapped by prefix
        """
        if self.size == 1:
            return self.addr, 0
        else:
            subAddrBits = (self.size - 1).bit_length()
        
        if self.addr & Bitmask.mask(subAddrBits):
            # is addr is not aligned to size
            return None
        return self.addr >> subAddrBits, subAddrBits

            
    def __repr__(self):
        if self.children:
            children = ",\n" + pprint.pformat(self.children, 2) + "\n "
        else:
            children = ""
        
        return "<AddrSpaceItem %s, %d, size=%d%s>" % (self.name, self.addr, self.size, children)