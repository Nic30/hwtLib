from typing import Optional, Tuple, Union, Type, Callable, Sequence

from hwt.code import If
from hwt.hwIO import HwIO
from hwt.hwIOs.std import HwIODataRdVld, HwIOClk, HwIORst, HwIORst_n
from hwt.hwModule import HwModule
from hwt.hdl.types.bits import HBits
from hwt.mainBases import RtlSignalBase
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwtLib.abstract.componentBuilder import AbstractComponentBuilder


class AbstractStreamBuilder(AbstractComponentBuilder):
    """
    :note: see :class:`AbstractComponentBuilder`
    :attention: this is just abstract class unit classes has to be specified
        in concrete implementation

    :cvar ~.FifoCls: FIFO unit class
    :cvar ~.FifoAsyncCls: asynchronous FIFO (FIFO with separate clock per port) unit class
    :cvar ~.JoinSelectCls: select order based join unit class
    :cvar ~.JoinFairCls: round robin based join unit class
    :cvar ~.JoinPrioritizedCls: priority based join unit class
    :cvar ~.RegCls: register unit class
    :cvar ~.RegCdcCls: Clock domain crossing register unit class
    :cvar ~.ResizerCls: resizer unit class (used to change data width of an interface)
    :cvar ~.SplitCopyCls: copy based split unit class
    :cvar ~.SplitSelectCls: select order based split unit class (demultiplexer)
    :cvar ~.SplitFairCls: round robin based split unit class
    :cvar ~.SplitPrioritizedCls: priority based split unit class
    """
    FifoCls = NotImplemented
    FifoAsyncCls = NotImplemented
    JoinSelectCls = NotImplemented
    JoinPrioritizedCls = NotImplemented
    JoinFairCls = NotImplemented
    RegCls = NotImplemented
    ResizerCls = NotImplemented
    SplitCopyCls = NotImplemented
    SplitSelectCls = NotImplemented
    SplitFairCls = NotImplemented
    SplitPrioritizedCls = NotImplemented

    def _genericInstance(self,
                         hwModuleCls: Type[HwModule],
                         name: str,
                         set_params_fn:Optional[Callable[[HwModule], None]]=None,
                         update_params=True,
                         propagate_clk_rst=True):
        """
        Instantiate generic component and connect basics

        :param hwModuleCls: class of HMoudule which is being created
        :param name: name for hwModuleCls instance
        :param set_params_fn: function which updates parameters as is required
            (parameters are already shared with self.end interface)
        """
        assert hwModuleCls is not NotImplemented
        m = hwModuleCls(self.getHwIOCls())
        if update_params:
            m._updateHwParamsFrom(self.end)
        if set_params_fn is not None:
            set_params_fn(m)

        setattr(self.parent, self._findSuitableName(name), m)
        if propagate_clk_rst:
            self._propagateClkRstn(m)

        self.lastComp = m

        if self.master_to_slave:
            m.dataIn(self.end)
            self.end = m.dataOut
        else:
            self.end(m.dataOut)
            self.end = m.dataIn

        return self

    @classmethod
    def _join(cls, joinCls: Type[HwModule],
               parent: HwModule,
               srcHwIOs: Sequence[HwIO],
               name: Optional[str],
               configAs: Optional[HwModule],
               extraConfigFn: Optional[Callable[[HwModule], None]]):
        """
        Create builder from many interfaces by joining them together

        :param joinCls: join component class which should be used
        :param parent: unit where builder should place components
        :param srcInterfacecs: sequence of interfaces which should be joined
            together (lower index = higher priority)
        :param configureAs: interface or another object which configuration
            should be applied
        :param extraConfigFn: function which is applied on join unit
            in configuration phase (can be None)
        """
        srcHwIOs = list(srcHwIOs)
        if name is None:
            if configAs is None:
                name = "gen_join"
            else:
                name = "gen_" + configAs._name

        if configAs is None:
            configAs = srcHwIOs[0]

        self = cls(parent, None, name=name)

        m = joinCls(self._getHwIOCls(configAs))
        if extraConfigFn is not None:
            extraConfigFn(m)
        m._updateHwParamsFrom(configAs)
        m.INPUTS = len(srcHwIOs)

        setattr(self.parent, self._findSuitableName(name + "_join"), m)
        self._propagateClkRstn(m)

        for joinIn, inputHwIO in zip(m.dataIn, srcHwIOs):
            joinIn(inputHwIO)

        self.lastComp = m
        self.end = m.dataOut

        return self

    @classmethod
    def join_prioritized(cls, parent: HwModule, srcInterfaces, name: Optional[str]=None,
                         configAs: Optional[HwModule]=None, extraConfigFn:Optional[Callable[[HwModule], None]]=None):
        """
        create builder from fairly joined interfaces (round robin for input select)

        :note: other parameters same as in `.AbstractStreamBuilder._join`
        """
        return cls._join(cls.JoinPrioritizedCls, parent, srcInterfaces, name,
                         configAs, extraConfigFn)

    @classmethod
    def join_fair(cls, parent, srcInterfaces, name=None,
                  configAs=None, exportSelected=False,
                  extraConfigFn:Optional[Callable[[HwModule], None]]=None):
        """
        create builder from fairly joined interfaces (round robin for input select)

        :param exportSelected: if True join component will have handshaked interface
            with index of selected input
        :note: other parameters same as in `.AbstractStreamBuilder._join`
        """

        def extraConfig(m):
            m.EXPORT_SELECTED = exportSelected
            if extraConfigFn is not None:
                extraConfigFn(m)

        return cls._join(cls.JoinFairCls, parent, srcInterfaces, name,
                         configAs, extraConfig)

    def buff(self, items:int=1,
             latency: Union[None, int, Tuple[int, int]]=None,
             delay: Optional[int]=None,
             init_data: tuple=()):
        """
        Use registers and FIFOs to create buffer of specified parameters
        :note: if items <= latency registers are used else FIFO is used

        :param items: number of items in buffer
        :param latency: latency of buffer (number of clk ticks required to get data
            from input to input)
        :param delay: delay of buffer (number of clk ticks required to get data to buffer)
        :note: delay can be used as synchronization method or to solve timing related problems
            because it will split valid signal path
        :param init_data: a reset value of buffer (data is transfered after reset)
            if items=1 and interface has just data:uint8_t signal
            the init_data will be in format ((0,),)
        :note: if latency or delay is None the most optimal value is used
        """
        if items == 0:
            assert latency is None or latency == 0
            assert delay is None or delay == 0
            return self

        elif items == 1:
            if latency is None:
                latency = 1
            if delay is None:
                delay = 0
        else:
            if latency is None:
                latency = 2
            if delay is None:
                delay = 0

        if init_data is not None:
            init_data = tuple(init_data)
            assert len(init_data) <= items, (items, "more init data than init size", init_data)

        assert isinstance(latency, tuple) or latency >= 1 and delay >= 0, (latency, delay)

        if isinstance(latency, tuple) or latency == 1 or latency >= items:

            # instantiate buffer as register
            def applyParams(u):
                u.LATENCY = latency
                u.DELAY = delay
                u.INIT_DATA = init_data

            return self._genericInstance(self.RegCls, "reg",
                                         set_params_fn=applyParams)
        else:
            # instantiate buffer as fifo
            if latency != 2 or delay != 0:
                raise NotImplementedError()

            def applyParams(u):
                u.DEPTH = items
                u.INIT_DATA = init_data

            return self._genericInstance(self.FifoCls, "fifo", applyParams)

    def buff_cdc(self,
                 clk: Union[HwIOClk, RtlSignal],
                 rst: Union[HwIORst, HwIORst_n, RtlSignal], items:int=1):
        """
        Instantiate a CDC (Clock Domain Crossing) buffer or AsyncFifo
        on selected interface

        :note: if items==1 CDC clock synchronization register is used
            if items>1 asynchronous FIFO is used
        """
        in_clk = self.getClk()
        in_rst_n = self.getRstn()
        if not self.master_to_slave:
            in_clk, clk = clk, in_clk
            in_rst_n, rst = rst, in_rst_n

        def set_clk_freq(u):
            u.IN_FREQ = in_clk.FREQ
            u.OUT_FREQ = clk.FREQ

        if items > 1:

            def configure(m):
                m.DEPTH = items
                set_clk_freq(m)

            res = self._genericInstance(
                self.FifoAsyncCls, "cdcAFifo", configure,
                propagate_clk_rst=False)
        else:
            assert items == 1, items
            res = self._genericInstance(
                self.RegCdcCls, "cdcReg", set_clk_freq,
                propagate_clk_rst=False)

        b = res.lastComp
        b.dataIn_clk(in_clk)
        b.dataIn_rst_n(in_rst_n)
        b.dataOut_clk(clk)
        b.dataOut_rst_n(rst)

        return res

    def split_copy(self, noOfOutputs: int):
        """
        Clone input data to all outputs

        :param noOfOutputs: number of output interfaces of the split
        """
        if not self.master_to_slave:
            assert len(self.end) == noOfOutputs, self.end

        def setChCnt(u):
            u.OUTPUTS = noOfOutputs

        return self._genericInstance(self.SplitCopyCls, 'splitCopy', setChCnt)

    def split_copy_to(self, *outputs: Sequence[HwIO]):
        """
        Same like split_copy, but outputs are automatically connected

        :param outputs: ports on which should be outputs
            of split component connected to
        """
        assert self.master_to_slave, "This function does not make sense if building in reverse order"
        noOfOutputs = len(outputs)
        s = self.split_copy(noOfOutputs)

        for toComponent, fromFork in zip(outputs, self.end):
            toComponent(fromFork)

        self.end = None  # invalidate None because port was fully connected
        return s

    def split_select(self, outputSelSignalOrSequence: Union[Sequence[RtlSignalBase], RtlSignalBase], noOfOutputs:int):
        """
        Create a de-multiplexer with number of outputs specified by noOfOutputs

        :param noOfOutputs: number of outputs of multiplexer
        :param outputSelSignalOrSequence: handshaked interface (onehot encoded)
            to control selected output or sequence of output indexes
            which should be used (will be repeated)
        """
        if not self.master_to_slave:
            assert len(self.end) == noOfOutputs, self.end

        def setChCnt(u):
            u.OUTPUTS = noOfOutputs

        self._genericInstance(self.SplitSelectCls, 'select', setChCnt)
        if isinstance(outputSelSignalOrSequence, HwIODataRdVld):
            self.lastComp.selectOneHot(outputSelSignalOrSequence)
        else:
            seq = outputSelSignalOrSequence
            t = HBits(self.lastComp.selectOneHot.data._dtype.bit_length())
            size = len(seq)
            ohIndexes = map(lambda x: 1 << x, seq)
            indexes = self.parent._sig(self.name + "split_seq",
                                       t[size],
                                       def_val=ohIndexes)
            actual = self.parent._reg(self.name + "split_seq_index",
                                      HBits(size.bit_length()),
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

    def split_select_to(self,
                        outputSelSignalOrSequence: Union[Sequence[RtlSignalBase], RtlSignalBase],
                        *outputs: Sequence[HwIO]):
        """
        Same like split_select, but outputs are automatically connected

        :param outputs: ports on which should be outputs of split component connected to
        """
        assert self.master_to_slave, "This function does not make sense if building in reverse order"

        noOfOutputs = len(outputs)
        s = self.split_select(outputSelSignalOrSequence, noOfOutputs)

        for toComponent, fromFork in zip(outputs, self.end):
            toComponent(fromFork)

        self.end = None  # invalidate None because port was fully connected
        return s

    def split_prioritized(self, noOfOutputs:int):
        """
        data from input is send to output which is ready and has highest priority from all ready outputs

        :param noOfOutputs: number of output interfaces of the fork
        """
        if not self.master_to_slave:
            assert len(self.end) == noOfOutputs, self.end

        def setChCnt(u):
            u.OUTPUTS = noOfOutputs

        self._genericInstance(self.SplitPrioritizedCls, 'splitPrio', setChCnt)
        return self

    def split_prioritized_to(self, *outputs: Sequence[HwIO]):
        """
        Same like split_prioritized, but outputs are automatically connected

        :param outputs: ports on which should be outputs of split component connected to
        """
        assert self.master_to_slave, "This function does not make sense if building in reverse order"
        noOfOutputs = len(outputs)

        s = self.split_prioritized(noOfOutputs)
        for toComponent, fromFork in zip(outputs, self.end):
            toComponent(fromFork)

        self.end = None  # invalidate None because port was fully connected
        return s

    def split_fair(self, noOfOutputs: int, exportSelected=False):
        """
        Create a round robin selector with number of outputs specified by noOfOutputs

        :param noOfOutputs: number of outputs of multiplexer
        :param exportSelected: if is True split component will have interface "selectedOneHot"
            of type VldSynced wich will have one hot index of selected item
        """
        if not self.master_to_slave:
            assert len(self.end) == noOfOutputs, self.end

        def setChCnt(u):
            u.OUTPUTS = noOfOutputs

        self._genericInstance(self.SplitFairCls, 'splitFair', setChCnt)
        return self

    def split_fair_to(self, *outputs: Sequence[HwIO], exportSelected=False):
        """
        Same like split_fair, but outputs are automatically connected

        :param outputs: ports on which should be outputs
            of split component connected to
        :param exportSelected: if is True split component will
            have interface "selectedOneHot" of type VldSynced
            which will have one hot index of selected item
        """
        assert self.master_to_slave, "This function does not make sense if building in reverse order"

        noOfOutputs = len(outputs)

        s = self.split_fair(noOfOutputs, exportSelected=exportSelected)
        for toComponent, fromFork in zip(outputs, self.end):
            toComponent(fromFork)

        self.end = None  # invalidate None because port was fully connected
        return s
