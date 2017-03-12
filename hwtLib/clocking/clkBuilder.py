from hwtLib.clocking.timers import TimerInfo
from hwt.synthesizer.param import evalParam
from hwt.hdlObjects.types.defs import BIT
from hwt.code import If, log2ceil
from hwt.synthesizer.interfaceLevel.unitImplHelpers import getSignalName
from hwt.hdlObjects.typeShortcuts import vecT


class ClkBuilder(object):
    
    def __init__(self, parent, srcInterface, name=None):
        """
        @param parent: unit in which will be all units created by this builder instanciated
        @param name: prefix for all instantiated units
        @param srcInterface: input clock
        """
        self.parent = parent
        self.lastComp = None
        self.end = srcInterface
        if name is None:
            name = "gen_" + getSignalName(srcInterface)
            
        self.name = name
        self.compId = 0
        
    def timers(self, periods, enableSig=None):
        """
        generate counters specified by count of iterations
        @param periods: list of integers/params which specifies periods of timers  
        @param enableSig: enable signal for counters
        @attention: if tick of timer his high and enable Sig falls low tick will stay high
        
        @return: list of tick signals from timers
        """
        timers = [TimerInfo(i) for i in periods]
        TimerInfo.resolveSharing(timers)
        TimerInfo.instantiate(self.parent, timers, enableSig=enableSig)
        
        return list(map(lambda timer: timer.tick, timers))
    
    def oversample(self, sig, sampleCount, sampleTick):
        """
        [TODO] last sample is not sampled correctly
        """
        if sig._dtype != BIT:
            raise  NotImplementedError()
        n = getSignalName(sig)
        
        sCnt = evalParam(sampleCount).val
        sampleDoneTick = self.timers([sampleCount],
                                     enableSig=sampleTick)[0]
        oversampleCntr = self.parent._reg(n + "_oversample_cntr%d" % (sCnt),
                                          vecT(log2ceil(sampleCount)+1, False),
                                          defVal=0)
        
        If(sampleTick,
            If(sampleDoneTick,
                oversampleCntr ** 0
            ).Elif(sig,
                oversampleCntr ** (oversampleCntr + 1)
            )
        )
        
        oversampled = self.parent._sig(n + "_oversampled%d" % (sCnt))
        oversampled ** (oversampleCntr > (sampleCount // 2 - 1))
        return oversampled, sampleDoneTick
