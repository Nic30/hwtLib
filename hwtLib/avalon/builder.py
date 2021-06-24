from hwtLib.abstract.componentBuilder import AbstractComponentBuilder
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.axi_comp.builder import AxiBuilder
from hwtLib.avalon.mmToAxi import AvalonMm_to_Axi4
from hwtLib.avalon.mm_buff import AvalonMmBuff


class AvalonMmBuilder(AbstractComponentBuilder):
    """
    Helper class wich simplifies instantiation and configuration
    of common components for AvalonMM interfaces
    """

    BuffCls = AvalonMmBuff

    def _genericInstance(self,
                         unit_cls,
                         name,
                         set_params=lambda u: u,
                         update_params=True,
                         propagate_clk_rst=True):
        """
        Instantiate generic component and connect basics

        :param unit_cls: class of unit which is being created
        :param name: name for unit_cls instance
        :param set_params: function which updates parameters as is required
            (parameters are already shared with self.end interface)
        """

        u = unit_cls()
        if update_params:
            u._updateParamsFrom(self.end)
        set_params(u)

        setattr(self.parent, self._findSuitableName(name), u)
        if propagate_clk_rst:
            self._propagateClkRstn(u)

        u.s(self.end)

        self.lastComp = u
        self.end = u.m

        return self

    def buff(self, addr_items=1, data_items=1):
        return AxiBuilder.buff(self, addr_items=addr_items, data_items=data_items)

    def to_axi(self, axi_cls, id_width=0):

        def applyParams(u: AvalonMm_to_Axi4):
            u.ID_WIDTH = id_width

        b = self._genericInstance(AvalonMm_to_Axi4, "avmm_to_axi4", set_params=applyParams)
        b = AxiBuilder(self.parent, b.end, self.name, self.master_to_slave)
        if axi_cls is Axi4:
            return b
        else:
            return b.to_axi(axi_cls, id_width=id_width)

