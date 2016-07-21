from hdl_toolkit.synthetisator.codeOps import connect


class AbstractStreamBuilder():
    """
    @attention: this is just abstract class unit classes has to be specified
    
    @cvar ForkCls: fork unit class
    @cvar FifoCls: fifo unit class
    @cvar RegCls : register unit class
    @cvar MuxCls : multiplexer unit class
    
    @ivar compId: used for sequential number of components
    @ivar lastComp: last builded component
    @ivar end     : last interface of data-path
    
    @attention: input port is taken from self.end
    """
    
    def __init__(self, parent, name, srcInterface):
        """
        @param parent: unit in which will be all units created by this builder instanciated
        @param name: prefix for all instantiated units
        @param srcInterface: start of data-path
        """
        self.parent = parent
        self.lastComp = None
        self.end = srcInterface
        self.name = name
        self.compId = 0
    
    def getClk(self):
        return self.parent.clk
    
    def getRstn(self):
        return self.parent.rst_n
    
    def getInfCls(self):
        return self.end.__class__
    
    def _genericInstance(self, unitCls, unitName, setParams= lambda u: u ):
        """
        @param unitCls: class of unit which is being created
        @param unitName: name for unitCls
        @param setParams: function which updates parameters as is required 
                        (parameters are already shared with self.end interface)
        """
        
        u = unitCls(self.getInfCls())
        u._updateParamsFrom(self.end)
        setParams(u)
        
        setattr(self.parent, "%s_%s_%d" % (self.name, unitName, self.compId), u)
        
        
        self.compId += 1
        
        connect(self.getClk(), u.clk)
        connect(self.getRstn(), u.rst_n)
        connect(self.end, u.dataIn)
        
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
        
        for In, Out in zip(outPorts, self.end):
            connect(Out, In)
            
        self.end = None # invalidate None because port was fully connected
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