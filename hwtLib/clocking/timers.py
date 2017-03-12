from hwt.code import log2ceil, If, isPow2
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import Signal
from hwt.interfaces.utils import addClkRstn
from hwt.pyUtils.arrayQuery import where
from hwt.synthesizer.interfaceLevel.unitImplHelpers import getClk
from hwt.synthesizer.param import evalParam



class TimerInfo(object):
    """
    @ivar cntrRegister: counter register for this timer
    @ivar tick: signal with tick from this timer
    @ivar parent: parent TimerInfo object from which this timer can be generated
    @ivar maxValOriginal: original value of maxVal
    @ivar maxVal: evaluated value of maxVal
    """
    __slots__ = ['maxVal', 'maxValOriginal', 'parent', 'cntrRegister', 'tick']
    
    def __init__(self, maxVal):
        self.maxValOriginal = maxVal 
        self.maxVal = evalParam(maxVal).val
        self.parent = None
        
    @staticmethod
    def resolveSharing(timers):
        # filter out timers with maxVal == 1 because they are only clock
        timers = sorted(where(timers,
                              lambda t: t.maxVal != 1),
                        key=lambda t: t.maxVal, reverse=True)
        for i, t in enumerate(timers):
            if isPow2(t.maxVal):
                # this timer will be driven from bit of some larger
                # counter if there is suitable
                for possibleParent in timers[:i]:
                    if possibleParent.maxVal % t.maxVal == 0:
                        if possibleParent.parent is not None:
                            continue
                        t.parent = possibleParent
                        break
            else:
                # this timer will have its own timer which will be enabled by 
                # some other timer if there is suitable
                for possibleParent in timers[(i + 1):]:
                    if t.maxVal % possibleParent.maxVal == 0:
                        if possibleParent.parent is t:
                            continue
                        t.parent = possibleParent
                        break
                
        # raise NotImplementedError()

    @staticmethod
    def _instantiateTimer(parentUnit, timer, enableSig=None):
        if timer.parent is None:
            maxVal = timer.maxVal - 1
            assert maxVal >= 0
            timer.tick = parentUnit._sig("timerTick%d" % timer.maxVal)

            if maxVal == 0:
                timer.tick ** 1
            else:
                r = parentUnit._reg("timerCntr%d" % timer.maxVal,
                                vecT(log2ceil(maxVal + 1)),
                                maxVal
                                )
                timer.cntrRegister = r
                nLogic = If(r._eq(0),
                             r ** (timer.maxValOriginal - 1)  # use original to propagate parameter
                         ).Else(
                             r ** (r - 1)
                         )
                if enableSig is not None:
                    If(enableSig,
                       nLogic
                    )
                
                timer.tick ** r._eq(0)
        else:
            p = timer.parent
            if not hasattr(p, "tick"):
                TimerInfo._instantiateTimer(parentUnit, p)
            assert hasattr(p, "tick")
            
            if p.maxVal == timer.maxVal:
                timer.cntrRegister = p.cntrRegister 
                timer.tick = p.tick
            elif p.maxVal < timer.maxVal:
                maxVal = (timer.maxVal // p.maxVal) - 1
                assert maxVal >= 0
                timer.tick = parentUnit._sig("timerTick%d" % timer.maxVal)
    
                r = parentUnit._reg("timerCntr%d" % timer.maxVal,
                                vecT(log2ceil(maxVal + 1)),
                                maxVal
                                )
                timer.cntrRegister = r
                if enableSig is None:
                    tick = p.tick
                else:
                    tick = p.tick & enableSig
                If(tick,
                    If(r._eq(0),
                        r ** ((timer.maxValOriginal // p.maxValOriginal) - 1)  # use original to propagate parameter
                    ).Else(
                        r ** (r - 1)
                    )
                )
                timer.tick ** (r._eq(0) & p.tick)
    
            else:
                # take specific bit from wider counter
                assert isPow2(timer.maxVal), timer.maxVal
                bitIndx = log2ceil(timer.maxVal)
                timer.cntrRegister = p.cntrRegister 
                timer.tick = p.cntrRegister[bitIndx]

    @staticmethod
    def instantiate(parentUnit, timers, enableSig=None):
        for timer in timers:
            if not hasattr(timer, "tick"):
                TimerInfo._instantiateTimer(parentUnit, timer, enableSig=enableSig)
            
    def __repr__(self):
        return "<%s maxVal=%d>" % (self.__class__.__name__, self.maxVal)
    
                
if __name__ == "__main__":
    from hwt.synthesizer.interfaceLevel.unit import Unit
    from hwt.synthesizer.shortcuts import toRtl
    from hwtLib.clocking.clkBuilder import ClkBuilder
    
    class TimerInfoTest(Unit):
        def _declr(self):
            addClkRstn(self)
            
            self.tick1 = Signal()
            self.tick2 = Signal()
            self.tick16 = Signal()

            self.tick17 = Signal()
            self.tick34 = Signal()
            
            self.tick256 = Signal()
            
            self.tick384 = Signal()
        
        def _impl(self):
            tick1, tick2, tick16, tick17, tick34, tick256, tick384 = ClkBuilder(self, self.clk)\
                                                                        .timers([1, 2, 16, 17, 34, 256, 384])
            self.tick1 ** tick1
            self.tick2 ** tick2
            self.tick16 ** tick16
            
            self.tick17 ** tick17
            self.tick34 ** tick34
            
            self.tick256 ** tick256
            self.tick384 ** tick384
    u = TimerInfoTest()
    print(toRtl(u))  
