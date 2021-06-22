from typing import Optional

from hwtLib.amba.axi4Lite import Axi4Lite
from hwtLib.amba.axi_comp.builder import AxiBuilder
from hwtLib.cesnet.mi32.axi4Lite_to_mi32 import Axi4Lite_to_Mi32
from hwtLib.cesnet.mi32.buff import Mi32Buff
from hwtLib.cesnet.mi32.intf import Mi32
from hwtLib.cesnet.mi32.sliding_window import Mi32SlidingWindow
from hwtLib.cesnet.mi32.to_axi4Lite import Mi32_to_Axi4Lite


class _Mi32Buff(Mi32Buff):
    """Mi32Buff constructor which ignores interface in constructor"""

    def __init__(self, intfCls, hdl_name_override:Optional[str]=None):
        assert intfCls is Mi32
        super(_Mi32Buff, self).__init__(hdl_name_override=hdl_name_override)


class Mi32Builder(AxiBuilder):

    BuffCls = _Mi32Buff
    BuffCdcCls = NotImplemented

    def sliding_window(self, window_size: int, new_addr_width: int):
        """
        Instanciate a sliding window with an offset register which allows to virtually
        extend the addressable memory space
        """
        end = self.end
        u = Mi32SlidingWindow()
        u.ADDR_WIDTH = end.ADDR_WIDTH
        u.DATA_WIDTH = end.DATA_WIDTH
        u.WINDOW_SIZE = window_size
        u.M_ADDR_WIDTH = new_addr_width

        setattr(self.parent, self._findSuitableName("mi32SlidingWindow"), u)
        self._propagateClkRstn(u)

        u.s(self.end)

        self.lastComp = u
        self.end = u.m
        return self

    @classmethod
    def from_axi(cls, parent, axi, name=None):
        """
        convertor AXI/AxiLite -> Mi32
        """
        axi_builder = AxiBuilder(parent, axi, name)
        end = axi_builder.end
        u = Axi4Lite_to_Mi32()
        u.ADDR_WIDTH = end.ADDR_WIDTH
        u.DATA_WIDTH = end.DATA_WIDTH

        setattr(parent, axi_builder._findSuitableName("axi_to_mi32"), u)
        axi_builder._propagateClkRstn(u)

        u.s(axi_builder.end)

        mi32_builder = cls(parent, u.m, name)
        mi32_builder.lastComp = u

        return mi32_builder

    def to_axi(self, axi_cls):
        """
        convertor Mi32 -> AXI/AXILite
        """
        end = self.end
        if axi_cls is Axi4Lite:
            u = Mi32_to_Axi4Lite()
        else:
            raise NotImplementedError(axi_cls)
        u.ADDR_WIDTH = end.ADDR_WIDTH
        u.DATA_WIDTH = end.DATA_WIDTH

        setattr(self.parent, self._findSuitableName("mi32_to_axi"), u)
        self._propagateClkRstn(u)

        u.s(self.end)

        self.lastComp = u
        self.end = u.m

        return AxiBuilder(self.parent, self.end, self.name)
