from hwt.synthesizer.param import evalParam


class TimerInfo(object):
    """
    @ivar register: counter register for this timer
    @ivar tick: signal with tick from this timer
    @ivar parent: parent TimerInfo object from which this timer can be generated
    @ivar maxValOriginal: original value of maxVal
    @ivar maxVal: evaluated value of maxVal
    """
    __slots__ = ['maxVal', 'maxValOriginal', 'parent', 'register', 'tick']
    
    def __init__(self, maxVal):
        self.maxValOriginal = maxVal 
        self.maxVal = evalParam(maxVal).val
        self.parent = None
        
    @staticmethod
    def resolveSharing(timers):
        raise NotImplementedError()
    
    @staticmethod
    def instantiate(parent, timers):
        raise NotImplementedError()

def timers(parent, countsOfIteration):
    timers = [TimerInfo(i) for i in countsOfIteration]
    TimerInfo.resolveSharing(timers)
    TimerInfo.instantiate(parent, timers)
    
    return list(map(lambda timer: timer.tick, timers))