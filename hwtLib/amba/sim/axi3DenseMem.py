from hwtLib.abstract.denseMemory import DenseMemory
from hwt.synthesizer.param import evalParam
from hwt.bitmask import mask


class Axi3DenseMem(DenseMemory):
    def __init__(self, clk, axi, parent=None):
        DW = evalParam(axi.DATA_WIDTH).val
        self.cellSize = DW // 8
        self.allMask = mask(self.cellSize)

        self.parent = parent
        if parent is None:
            self.data = {}
        else:
            self.data = parent.data

        self.arAg = axi._ag.ar
        self.rAg = axi._ag.r

        self.rPending = []

        self.awAg = axi._ag.aw
        self.wAg = axi._ag.w
        self.wAckAg = axi._ag.b
        self.wPending = []

        self._registerOnClock(clk)
