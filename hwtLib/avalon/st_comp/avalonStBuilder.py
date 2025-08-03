from typing import Optional

from hwt.hwModule import HwModule
from hwtLib.amba.axi4s import Axi4Stream
from hwtLib.amba.axis_comp.builder import Axi4SBuilder
from hwtLib.avalon.st_comp.avalonStLatencyAdapter import AvalonST_latencyAdapter
from hwtLib.avalon.st_comp.avalonStToAxi4s import AvalonST_to_Axi4Stream
from hwtLib.handshaked.builder import HsBuilder
from hwtLib.avalon.st_comp.axi4sToAvalonSt import Axi4Stream_to_AvalonST


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

    def to_axis(self) -> Axi4SBuilder:
        if self.name:
            name = f"{self.name:s}_toAxi4stream"
        else:
            name = "gen_toAxi4stream"

        if self.end.readyAllowance != 0 or self.end.readyLatency != 0:
            self.castReadyLatencyAndAllowance(0, 0)

        self._genericInstance(lambda _: AvalonST_to_Axi4Stream(), name)
        return Axi4SBuilder(self.parent, self.end, self.name)

    @classmethod
    def from_axis(cls, parent: HwModule, src: Axi4Stream, name:Optional[str]=None):
        if name is None:
            name = f"gen_{src._name}"

        self = cls(parent, None, name)
        if self.name:
            name = f"{self.name:s}_fromAxi4S"
        else:
            name = "gen_fromAxi4S"

        def set_params_fn(m: Axi4Stream_to_AvalonST):
            m._updateHwParamsFrom(src)

        self._genericInstance(lambda _: Axi4Stream_to_AvalonST(),
                              name,
                              set_params_fn,
                              update_params=False,
                              connect_in_out=False)
        self.lastComp.dataIn(src)
        self.end = self.lastComp.dataOut

        return self

