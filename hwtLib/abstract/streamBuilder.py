from hwt.synthesizer.interfaceLevel.unitImplHelpers import getClk, getRst
from hwt.interfaces.std import Rst_n
from enum import Enum


class JOIN_MODE(Enum):
    ITERATIVE = 0  # input from index 0, 1,... etc if input is not ready all waits
    PRIORITY = 1  # input with lowest lower index has priority 
    FAIR_SHARE = 2  # priority flag is cycling on inputs, round robin like 
    # SPECIAL_ORDER (use [ of numbers] or input handshaked interface with indexes)

class AbstractStreamBuilder(object):
    """
    :attention: this is just abstract class unit classes has to be specified in concrete implementation

    :cvar JoinCls: join unit class
    :cvar ForkCls: fork unit class
    :cvar FifoCls: fifo unit class
    :cvar RegCls: register unit class
    :cvar MuxCls: multiplexer unit class
    :cvar DemuxCls: demultiplexer unit class
    :cvar ResizerCls: resizer unit class

    :ivar compId: used for sequential number of components
    :ivar lastComp: last builded component
    :ivar end: last interface of data-path

    :attention: input port is taken from self.end
    """

    def __init__(self, parent, srcInterface, name=None):
        """
        :param parent: unit in which will be all units created by this builder instanciated
        :param name: prefix for all instantiated units
        :param srcInterface: start of data-path
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
        :param unitCls: class of unit which is being created
        :param unitName: name for unitCls
        :param setParams: function which updates parameters as is required
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

        :param parent: unit where builder should place components
        :param srcInterfacecs: iterable of interfaces which should be joined together (lower index = higher priority)
        :param configureAs: interface or another object which configuration should be applied
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

        setattr(self.parent, self._findSuitableName(name + "_join"), u)
        self._propagateClkRstn(u)

        for joinIn, inputIntf in zip(u.dataIn, srcInterfaces):
            joinIn ** inputIntf

        self.lastComp = u
        self.end = u.dataOut

        return self

    def fork(self, noOfOutputs):
        """
        creates fork - split one interface to many

        :param noOfOutputs: number of output interfaces of the fork
        """
        def setChCnt(u):
            u.OUTPUTS.set(noOfOutputs)

        return self._genericInstance(self.ForkCls, 'fork', setChCnt)

    def forkTo(self, *outPorts):
        """
        Same like fork, but outputs ports are automatically connected

        :param outPorts: ports on which should be outputs of fork connected
        """
        noOfOutputs = len(outPorts)
        s = self.fork(noOfOutputs)

        for toComponent, fromFork in zip(outPorts, self.end):
            toComponent ** fromFork

        self.end = None  # invalidate None because port was fully connected
        return s

    def reg(self, latency=1, delay=0):
        """
        Create register on interface
        """
        def applyParams(u):
            u.LATENCY.set(latency)
            u.DELAY.set(delay)
        return self._genericInstance(self.RegCls, "reg", setParams=applyParams)

    def fifo(self, depth):
        """
        Create synchronous fifo of the size of depth
        """
        def setDepth(u):
            u.DEPTH.set(depth)
        return self._genericInstance(self.FifoCls, "fifo", setDepth)

    def demux(self, noOfOutputs, outputSelSignal):
        """
        Create a demultiplexer with outputs specified by noOfOutputs

        :param noOfOutputs: number of outputs of multiplexer
        """
        def setChCnt(u):
            u.OUTPUTS.set(noOfOutputs)
            
        self._genericInstance(self.DemuxCls, 'demux', setChCnt)
        self.lastComp.sel ** outputSelSignal
        
        return self
