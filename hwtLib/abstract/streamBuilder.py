from hwt.code import If
from hwt.hdl.types.bits import Bits
from hwt.interfaces.std import Rst_n, Handshaked
from hwt.synthesizer.interfaceLevel.unitImplHelpers import getClk, getRst
from hwt.synthesizer.hObjList import HObjList


class AbstractStreamBuilder(object):
    """
    :attention: this is just abstract class unit classes has to be specified
        in concrete implementation

    :cvar FifoCls: fifo unit class
    :cvar JoinSelectCls: select order based join unit class
    :cvar JoinFairCls: round robin based join unit class
    :cvar JoinPrioritizedCls: priority based join unit class
    :cvar RegCls: register unit class
    :cvar ResizerCls: resizer unit class
    :cvar SplitCopyCls: copy based split unit class
    :cvar SplitSelectCls: select order based split unit class (demultiplexer)
    :cvar SplitFairCls: round robin based split unit class
    :cvar SplitPrioritizedCls: priority based split unit class

    :ivar compId: used for sequential number of components
    :ivar lastComp: last builded component
    :ivar end: last interface of data-path

    :attention: input port is taken from self.end
    """
    FifoCls = NotImplemented
    JoinSelectCls = NotImplemented
    JoinPrioritizedCls = NotImplemented
    JoinFairCls = NotImplemented
    RegCls = NotImplemented
    ResizerCls = NotImplemented
    SplitCopyCls = NotImplemented
    SplitSelectCls = NotImplemented
    SplitFairCls = NotImplemented
    SplitPrioritizedCls = NotImplemented

    def __init__(self, parent, srcInterface, name=None):
        """
        :param parent: unit in which will be all units created by this builder instantiated
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
        """
        lookup clock signal on parent
        """
        return getClk(self.parent)

    def getRstn(self):
        """
        lookup reset(n) signal on parent
        """
        rst = getRst(self.parent)
        if isinstance(rst, Rst_n):
            return rst
        else:
            return ~rst

    def getInfCls(self):
        """
        Get class of interface which this builder is currently using.
        """
        return self._getIntfCls(self.end)

    def _getIntfCls(self, intf):
        """
        Get real interface class of interface
        """
        if isinstance(intf, HObjList):
            return self._getIntfCls(intf[0])

        return intf.__class__

    def _findSuitableName(self, unitName):
        """
        find suitable name for component (= name without collisions)
        """
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
        """
        Connect clock and reset to unit "u"
        """
        if hasattr(u, "clk"):
            u.clk(self.getClk())

        if hasattr(u, 'rst_n'):
            u.rst_n(self.getRstn())

        if hasattr(u, "rst"):
            u.rst(~self.getRstn())

    def _genericInstance(self, unitCls, unitName, setParams=lambda u: u):
        """
        Instantiate generic component and connect basics

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

        u.dataIn(self.end)

        self.lastComp = u
        self.end = u.dataOut

        return self

    @classmethod
    def _join(cls, joinCls, parent, srcInterfaces, name, configAs, extraConfigFn):
        """
        Create builder from many interfaces by joining them together

        :param joinCls: join component class which should be used
        :param parent: unit where builder should place components
        :param srcInterfacecs: sequence of interfaces which should be joined together (lower index = higher priority)
        :param configureAs: interface or another object which configuration should be applied
        :param extraConfigFn: function which is applied on join unit in configuration phase (can be None)
        """
        srcInterfaces = list(srcInterfaces)
        if name is None:
            if configAs is None:
                name = "gen_join"
            else:
                name = "gen_" + configAs._name

        if configAs is None:
            configAs = srcInterfaces[0]

        self = cls(parent, None, name=name)

        u = joinCls(self._getIntfCls(configAs))
        if extraConfigFn is not None:
            extraConfigFn(u)
        u._updateParamsFrom(configAs)
        u.INPUTS = len(srcInterfaces)

        setattr(self.parent, self._findSuitableName(name + "_join"), u)
        self._propagateClkRstn(u)

        for joinIn, inputIntf in zip(u.dataIn, srcInterfaces):
            joinIn(inputIntf)

        self.lastComp = u
        self.end = u.dataOut

        return self

    @classmethod
    def join_fair(cls, parent, srcInterfaces, name=None, configAs=None, exportSelected=False):
        """
        create builder from fairly joined interfaces (round robin for input select)

        :param exportSelected: if True join component will have handshaked interface
            with index of selected input
        :note: other parameters same as in `.AbstractStreamBuilder.join_fair`
        """
        def extraConfig(u):
            u.EXPORT_SELECTED = exportSelected

        return cls._join(cls.JoinFairCls, parent, srcInterfaces, name, configAs, extraConfig)

    def buff(self, items=1, latency=None, delay=None):
        """
        Use registers and fifos to create buffer of specified paramters
        :note: if items <= latency registers are used else fifo is used

        :param items: number of items in buffer
        :param latency: latency of buffer (number of clk ticks required to get data
            from input to input)
        :param delay: delay of buffer (number of clk ticks required to get data to buffer)
        :note: delay can be used as synchronization method or to solve timing related problems
            because it will split valid signal path
        :note: if latency or delay is None the most optimal value is used
        """

        if items == 1:
            if latency is None:
                latency = 1
            if delay is None:
                delay = 0
        else:
            if latency is None:
                latency = 2
            if delay is None:
                delay = 0

        assert latency >= 1 and delay >= 0, (latency, delay)

        if latency == 1 or latency >= items:
            # instantiate buffer as register
            def applyParams(u):
                u.LATENCY = latency
                u.DELAY = delay
            return self._genericInstance(self.RegCls, "reg", setParams=applyParams)
        else:
            # instantiate buffer as fifo
            if latency != 2 or delay != 0:
                raise NotImplementedError()

            def setDepth(u):
                u.DEPTH = items
            return self._genericInstance(self.FifoCls, "fifo", setDepth)

    def split_copy(self, noOfOutputs):
        """
        Clone input data to all outputs

        :param noOfOutputs: number of output interfaces of the split
        """
        def setChCnt(u):
            u.OUTPUTS = noOfOutputs

        return self._genericInstance(self.SplitCopyCls, 'splitCopy', setChCnt)

    def split_copy_to(self, *outputs):
        """
        Same like split_copy, but outputs are automatically connected

        :param outputs: ports on which should be outputs of split component connected to
        """
        noOfOutputs = len(outputs)
        s = self.split_copy(noOfOutputs)

        for toComponent, fromFork in zip(outputs, self.end):
            toComponent(fromFork)

        self.end = None  # invalidate None because port was fully connected
        return s

    def split_select(self, outputSelSignalOrSequence, noOfOutputs):
        """
        Create a demultiplexer with number of outputs specified by noOfOutputs

        :param noOfOutputs: number of outputs of multiplexer
        :param outputSelSignalOrSequence: handshaked interface (onehot encoded)
            to control selected output or sequence of output indexes
            which should be used (will be repeated)
        """

        def setChCnt(u):
            u.OUTPUTS = noOfOutputs

        self._genericInstance(self.SplitSelectCls, 'select', setChCnt)
        if isinstance(outputSelSignalOrSequence, Handshaked):
            self.lastComp.selectOneHot(outputSelSignalOrSequence)
        else:
            seq = outputSelSignalOrSequence
            t = Bits(self.lastComp.selectOneHot.data._dtype.bit_length())
            size = len(seq)
            ohIndexes = map(lambda x: 1 << x, seq)
            indexes = self.parent._sig(self.name + "split_seq",
                                       t[size],
                                       def_val=ohIndexes)
            actual = self.parent._reg(self.name + "split_seq_index",
                                      Bits(size.bit_length()),
                                      0)
            iin = self.lastComp.selectOneHot
            iin.data(indexes[actual])
            iin.vld(1)
            If(iin.rd,
               If(actual._eq(size - 1),
                  actual(0)
               ).Else(
                  actual(actual + 1)
               )
            )

        return self

    def split_select_to(self, outputSelSignalOrSequence, *outputs):
        """
        Same like split_select, but outputs are automatically connected

        :param outputs: ports on which should be outputs of split component connected to
        """
        noOfOutputs = len(outputs)
        s = self.split_select(outputSelSignalOrSequence, noOfOutputs)

        for toComponent, fromFork in zip(outputs, self.end):
            toComponent(fromFork)

        self.end = None  # invalidate None because port was fully connected
        return s

    def split_prioritized(self, noOfOutputs):
        """
        data from input is send to output which is ready and has highest priority from all ready outputs

        :param noOfOutputs: number of output interfaces of the fork
        """
        def setChCnt(u):
            u.OUTPUTS = noOfOutputs

        self._genericInstance(self.SplitPrioritizedCls, 'splitPrio', setChCnt)
        return self

    def split_prioritized_to(self, *outputs):
        """
        Same like split_prioritized, but outputs are automatically connected

        :param outputs: ports on which should be outputs of split component connected to
        """
        noOfOutputs = len(outputs)

        s = self.split_prioritized(noOfOutputs)
        for toComponent, fromFork in zip(outputs, self.end):
            toComponent(fromFork)

        self.end = None  # invalidate None because port was fully connected
        return s

    def split_fair(self, noOfOutputs, exportSelected=False):
        """
        Create a rund robin selector with number of outputs specified by noOfOutputs

        :param noOfOutputs: number of outputs of multiplexer
        :param exportSelected: if is True split component will have interface "selectedOneHot"
            of type VldSynced wich will have one hot index of selected item
        """

        def setChCnt(u):
            u.OUTPUTS = noOfOutputs

        self._genericInstance(self.SplitFairCls, 'splitFair', setChCnt)
        return self

    def split_fair_to(self, *outputs, exportSelected=False):
        """
        Same like split_fair, but outputs are automatically connected

        :param outputs: ports on which should be outputs of split component connected to
        :param exportSelected: if is True split component will have interface "selectedOneHot"
            of type VldSynced wich will have one hot index of selected item
        """
        noOfOutputs = len(outputs)

        s = self.split_fair(noOfOutputs, exportSelected=exportSelected)
        for toComponent, fromFork in zip(outputs, self.end):
            toComponent(fromFork)

        self.end = None  # invalidate None because port was fully connected
        return s
