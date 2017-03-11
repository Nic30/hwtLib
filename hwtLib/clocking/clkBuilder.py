from hwtLib.clocking.timers import TimerInfo


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
            name = "gen_" + srcInterface._name 
            
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