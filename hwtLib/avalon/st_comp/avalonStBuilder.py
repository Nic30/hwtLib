from typing import Optional

from hwt.hwModule import HwModule
from hwtLib.avalon.st_comp.avalonStLatencyAdapter import AvalonST_latencyAdapter
from hwtLib.handshaked.builder import HsBuilder


class AvalonSTBuilder(HsBuilder):
    JoinExplicitCls = NotImplemented
    JoinPrioritizedCls = NotImplemented
    JoinFairCls = NotImplemented
    ResizerCls = NotImplemented
    SplitFairCls = NotImplemented
    SplitPrioritizedCls = NotImplemented
    SplitSelectCls = NotImplemented

    def castReadyLatencyAndAllowance(self, readyLatency:int, readyAllowance:Optional[int]=None):
        if self.name:
            name = f"{self.name:s}_latencyAdapter"
        else:
            name = "gen_latencyAdapter"

        def set_params_fn(m: AvalonST_latencyAdapter):
            m.OUT_readyAllowance = readyAllowance
            m.OUT_readyLatency = readyLatency

        self._genericInstance(lambda _: AvalonST_latencyAdapter(), name, set_params_fn)

        return self

