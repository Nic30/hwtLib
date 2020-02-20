from hwtLib.abstract.componentBuilder import AbstractComponentBuilder
from hwtLib.amba.axi_comp.axi_buff import AxiBuff
from hwtLib.amba.axi_comp.axi_buff_cdc import AxiBuffCdc
from hwtLib.amba.axi_comp.resize import AxiResize
from hwtLib.amba.axiLite_comp.axiLite_to_Axi import AxiLite_to_Axi


class AxiBuilder(AbstractComponentBuilder):
    """
    Helper class wich simplifies instantiation and configuration
    of common components for Axi interfaces
    """
    BuffCls = AxiBuff
    BuffCdcCls = AxiBuffCdc

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

        u = unit_cls(self.getInfCls())
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
        """
        Use registers and FIFOs to create buffer of specified paramters

        :param items: number of items in buffer
        """
        def applyParams(u: AxiBuff):
            u.ADDR_BUFF_DEPTH = addr_items
            u.DATA_BUFF_DEPTH = data_items

        return self._genericInstance(self.BuffCls, "buff",
                                     set_params=applyParams)

    def buff_cdc(self, clk, rst, addr_items=1, data_items=1):
        """
        Instanciate a CDC (Clock Domain Crossing) buffer or AsyncFifo
        on selected interface

        :note: if items==1 CDC clock synchronization register is used
            if items>1 asynchronous FIFO is used
        """
        current_clk = self.getClk()
        current_rst_n = self.getRstn()

        def applyParams(u: AxiBuffCdc):
            u.ADDR_BUFF_DEPTH = addr_items
            u.DATA_BUFF_DEPTH = data_items
            u.M_FREQ = current_clk.FREQ
            u.S_FREQ = clk.FREQ

        res = self._genericInstance(self.BuffCdcCls, "buffCdc",
                                    set_params=applyParams,
                                    propagate_clk_rst=False)
        b = res.lastComp
        b.clk(current_clk)
        b.rst_n(current_rst_n)

        b.m_clk(clk)
        if not rst._dtype.negated:
            rst = ~rst
        b.m_rst_n(rst)

        return res

    def resize(self, addr_width=None, data_width=None):
        end = self.end
        if data_width is None:
            data_width = end.DATA_WIDTH

        if addr_width is None:
            addr_width = end.ADDR_WIDTH

        if data_width == end.DATA_WIDTH and addr_width == end.ADDR_WIDTH:
            return self

        def set_params(u):
            u.OUT_DATA_WIDTH = data_width
            u.OUT_ADDR_WIDTH = addr_width

        return self._genericInstance(
            AxiResize, "resizer", set_params)

    def to_axi(self, axi_cls, id_width):
        if self.end.__class__ is axi_cls:
            return self

        def applyParams(u):
            u.ID_WIDTH = id_width

        get_intf_cls = self.getInfCls
        try:
            self.getInfCls = lambda: axi_cls
            return self._genericInstance(AxiLite_to_Axi, "axiLite_to_Axi",
                                         set_params=applyParams)
        finally:
            self.getInfCls = get_intf_cls
