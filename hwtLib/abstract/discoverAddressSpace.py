from hdl_toolkit.hdlObjects.operator import Operator
from hdl_toolkit.synthesizer.interfaceLevel.mainBases import UnitBase
from hwtLib.abstract.busConverter import BusConverter
from hdl_toolkit.hdlObjects.assignment import Assignment
from hdl_toolkit.hdlObjects.portItem import PortItem
from hdl_toolkit.hdlObjects.operatorDefs import AllOps
from copy import deepcopy, copy


def getEpSignal(sig, op):
    """
    @param sig: main signal
    @param op: operator on this signal
    
    @return: signal modified by this operator or none if this operator is creating new datapath
    """
    # we do not follow results of indexing like something[sig]
    if op.operator == AllOps.INDEX:
        if op.ops[0] is not sig:
            return
    if op.operator not in  [AllOps.INDEX, AllOps.ADD, AllOps.SUB, AllOps.MUL, AllOps.DIV, AllOps.CONCAT]:
        return
    
    if sig in op.ops:
        return op.result
    
    

def getParentUnit(sig):
    try: 
        intf = sig._interface
    except AttributeError:
        return  # if there is no interface it cant have parent unit
    
    while not isinstance(intf._parent, UnitBase):
        intf = intf._parent
    return intf._parent
    

class AddressSpaceProbe(object):
    def __init__(self, topIntf, getMainSigFn, offset=0):
        """
        @param topIntf: interface on which should discovery start
        @param getMainSigFn: function which gets the main signal
                 form interface which should this code care about
                 usually address 
        """
        self.topIntf = topIntf
        self.getMainSigFn = getMainSigFn
        self.offset = offset
    
    def discover(self):
        return self._discoverAddressSpace(self.topIntf, self.offset)
    
    @staticmethod
    def pprint(addrSpaceDict, indent=0):
        "pretty print"
        
        for addr in sorted(addrSpaceDict.keys()):
            item = addrSpaceDict[addr]
            if item.size > 1:
                size = "(size=%d)" % item.size
            else:
                size = ""
            _indent = "".join(["    " for _ in range(indent) ])
            print("%s0x%x:%s%s" % (_indent, addr, item.name, size))
            AddressSpaceProbe.pprint(item.children, indent + 1)
        
    
    def _extractAddressMap(self, converter, offset=0):
        """
        coppy address space map from converter
        """
        m = {}
        for item in converter._addrSpace:
            item = copy(item)
            
            if item.size > 1:
                port = getattr(converter, item.name)
                m[item.addr + offset] = item
                item.children = self._discoverAddressSpace(port, offset + item.addr)
            else:
                m[item.addr + offset] = item 
        return m

    def walkToConverter(self, mainSig, ignoreMyParent=False):
        """
        we walk mainSig down to endpoints and we are searching for any bus converter instance
        """
        if mainSig is None:
            return
        
        parent = getParentUnit(mainSig)
        if isinstance(parent, BusConverter) and not ignoreMyParent:
            yield parent
        
        for e in mainSig.endpoints:
            if isinstance(e, Operator):
                ep = getEpSignal(mainSig, e)
                if ep is not None:
                    yield from self.walkToConverter(ep)
            elif isinstance(e, (Assignment, PortItem)):
                if e.src is mainSig:
                    yield from self.walkToConverter(e.dst)
            else:
                raise NotImplementedError(e.__class__)
        
    def _discoverAddressSpace(self, topIntf, offset=0):
        _mainSig = self.getMainSigFn(topIntf) 
        try:
            mainSig = _mainSig._sig
        except AttributeError:
            mainSig = _mainSig._sigInside
        
        addrMap = {}
        for converter in self.walkToConverter(mainSig, ignoreMyParent=True):
            addrMap = self._extractAddressMap(converter, offset)        
            
        return addrMap
    


    
