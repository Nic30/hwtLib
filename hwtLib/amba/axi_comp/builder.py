from hwtLib.abstract.componentBuilder import AbstractComponentBuilder
from hwtLib.amba.axi_comp.axi_buff import AxiBuff
from hwtLib.amba.axi_comp.axi_buff_cdc import AxiBuffCdc


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

        u.m(self.end)

        self.lastComp = u
        self.end = u.s

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

        b.s_clk(clk)
        if not rst._dtype.negated:
            rst = ~rst
        b.s_rst_n(rst)

        return res
