from hwt.synthesizer.interfaceLevel.unitImplHelpers import getClk, getRst
from hwt.interfaces.std import Rst_n
getClk

class AbstractStreamBuilder():
    """
    @attention: this is just abstract class unit classes has to be specified in concrete implementation
    
    @cvar JoinCls: join unit class
    @cvar ForkCls: fork unit class
    @cvar ForkRegisteredCls: registered fork unit class
    @cvar FifoCls: fifo unit class
    @cvar RegCls : register unit class
    @cvar MuxCls : multiplexer unit class
    
    @ivar compId: used for sequential number of components
    @ivar lastComp: last builded component
    @ivar end     : last interface of data-path
    
    @attention: input port is taken from self.end
    """
    
    def __init__(self, parent, srcInterface, name=None):
        """
        @param parent: unit in which will be all units created by this builder instanciated
        @param name: prefix for all instantiated units
        @param srcInterface: start of data-path
        """
        self.parent = parent
        self.lastComp = None
        self.end = srcInterface
        if name is None:
            name = "gen_" + srcInterface._name 
            
        self.name = name
        self.compId = 0
    
    def getClk(self):
        return getClk(self.parent)
    
    def getRstn(self):
        rst = getRst(self.parent)
        if isinstance(rst, Rst_n):
            return rst
        else:
            return ~rst
        
    def getInfCls(self):
        return self.end.__class__
    
    def _findSuitableName(self, unitName):
        # find suitable name for component
        while True:
            name = "%s_%s_%d" % (self.name, unitName, self.compId)
            try:
                getattr(self.parent, name)
            except AttributeError:
                return name
                break
            self.compId += 1
        
        self.compId += 1
    
    def _propagateClkRstn(self, u):
        if hasattr(u, "clk"):
            u.clk ** self.getClk() 
        
        if hasattr(u, 'rst_n'):
            u.rst_n ** self.getRstn()

        if hasattr(u, "rst"):
            u.rst ** ~self.getRstn()
        
    
    def _genericInstance(self, unitCls, unitName, setParams=lambda u: u):
        """
        @param unitCls: class of unit which is being created
        @param unitName: name for unitCls
        @param setParams: function which updates parameters as is required 
                        (parameters are already shared with self.end interface)
        """
        
        u = unitCls(self.getInfCls())
        u._updateParamsFrom(self.end)
        setParams(u)
        
        setattr(self.parent, self._findSuitableName(unitName), u)
        self._propagateClkRstn(u)

        u.dataIn ** self.end 
        
        self.lastComp = u
        self.end = u.dataOut  
        
        return self
    
    @classmethod
    def join(cls, parent, srcInterfaces, name=None, configAs=None):
        """
        create builder from joined interfaces
        @param parent: unit where builder should place components
        @param srcInterfacecs: iterable of interfaces which should be joined together (lower index = higher priority)
        @param configureAs: interface or another object which configuration should be applied 
        """
        srcInterfaces = list(srcInterfaces)
        if configAs is None:
            configAs = srcInterfaces[0]
        
        if name is None:
            name = "gen_" + configAs._name 
            
        self = cls(parent, None, name=name)
        
        u = self.JoinCls(configAs.__class__)
        u._updateParamsFrom(configAs)
        u.INPUTS.set(len(srcInterfaces))
        
        setattr(self.parent, self._findSuitableName(name+"_join"), u)
        self._propagateClkRstn(u)

        for joinIn, inputIntf in zip(u.dataIn, srcInterfaces):
            joinIn ** inputIntf 
        
        self.lastComp = u
        self.end = u.dataOut  
        
        return self
        
    def fork(self, noOfOutputs):
        """
        creates fork - split one interface to many
        @param noOfOutputs: number of output interfaces of the fork
        """
        def setChCnt(u):
            u.OUTPUTS.set(noOfOutputs)
        
        return self._genericInstance(self.ForkCls, 'fork', setChCnt)
    
    def forkTo(self, *outPorts):
        """
        Same like fork, but outputs ports are automaticaly conected 
        @param outPorts: ports on which sodould be outputs of fork connected
        """
        noOfOutputs = len(outPorts) 
        s = self.fork(noOfOutputs)
        
        for toComponent, fromFork in zip(outPorts, self.end):
            toComponent ** fromFork
            
        self.end = None  # invalidate None because port was fully connected
        return s
    
    def reg(self):
        """
        Create register on interface
        """
        return self._genericInstance(self.RegCls, "reg")

    def fifo(self, depth):
        """
        Create synchronous fifo of the size of depth
        """
        def setDepth(u):
            u.DEPTH.set(depth)
        return self._genericInstance(self.FifoCls, "fifo", setDepth)
    
    def mux(self, noOfOutputs):
        """
        Create a multiplexer with outputs specified by noOfOutputs
        @param noOfOutputs: number of outputs of multiplexer
        """
        def setChCnt(u):
            u.OUTPUTS.set(noOfOutputs)
        
        return self._genericInstance(self.MuxCls, 'mux', setChCnt)
