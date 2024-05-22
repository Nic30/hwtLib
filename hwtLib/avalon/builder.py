from typing import Optional, Callable, Type

from hwt.hwModule import HwModule
from hwtLib.abstract.componentBuilder import AbstractComponentBuilder
from hwtLib.amba.axi4 import Axi4
from hwtLib.amba.axi_comp.builder import AxiBuilder
from hwtLib.avalon.mmToAxi import AvalonMm_to_Axi4
from hwtLib.avalon.mm_buff import AvalonMmBuff
from hwt.hwIO import HwIO


class AvalonMmBuilder(AbstractComponentBuilder):
    """
    Helper class wich simplifies instantiation and configuration
    of common components for AvalonMM interfaces
    """

    BuffCls = AvalonMmBuff

    def _genericInstance(self,
                         hwModuleCls: Type[HwModule],
                         name: str,
                         set_params_fn: Optional[Callable[[HwModule], None]]=None,
                         update_params:bool=True,
                         propagate_clk_rst:bool=True):
        """
        Instantiate generic component and connect basics

        :param hwModuleCls: class of unit which is being created
        :param name: name for hwModuleCls instance
        :param set_params_fn: function which updates parameters as is required
            (parameters are already shared with self.end interface)
        """

        m = hwModuleCls()
        if update_params:
            m._updateParamsFrom(self.end)
        if set_params_fn is not None:
            set_params_fn(m)

        setattr(self.parent, self._findSuitableName(name), m)
        if propagate_clk_rst:
            self._propagateClkRstn(m)

        m.s(self.end)

        self.lastComp = m
        self.end = m.m

        return self

    def buff(self, addr_items: int=1, data_items: int=1):
        return AxiBuilder.buff(self, addr_items=addr_items, data_items=data_items)

    def to_axi(self, axi_cls: HwIO, id_width: int=0):

        def applyParams(u: AvalonMm_to_Axi4):
            u.ID_WIDTH = id_width

        b = self._genericInstance(AvalonMm_to_Axi4, "avmm_to_axi4", set_params_fn=applyParams)
        b = AxiBuilder(self.parent, b.end, self.name, self.master_to_slave)
        if axi_cls is Axi4:
            return b
        else:
            return b.to_axi(axi_cls, id_width=id_width)

