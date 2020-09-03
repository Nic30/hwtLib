from hwtLib.amba.axi4Lite import Axi4Lite_addr, Axi4Lite_w, Axi4Lite_r,\
    Axi4Lite_b, Axi4Lite
from hwtLib.amba.axi_intf_common import Axi_id


class Axi4Lite_addr_withId(Axi4Lite_addr):

    def _config(self):
        Axi_id._config(self)
        Axi4Lite_addr._config(self)

    def _declr(self):
        Axi_id._declr(self)
        Axi4Lite_addr._declr(self)


class Axi4Lite_w_withId(Axi4Lite_w):

    def _config(self):
        Axi_id._config(self)
        Axi4Lite_w._config(self)

    def _declr(self):
        Axi_id._declr(self)
        Axi4Lite_w._declr(self)

    
class Axi4Lite_r_withId(Axi4Lite_r):

    def _config(self):
        Axi_id._config(self)
        Axi4Lite_r._config(self)

    def _declr(self):
        Axi_id._declr(self)
        Axi4Lite_r._declr(self)


class Axi4Lite_b_withId(Axi4Lite_b):

    def _config(self):
        Axi_id._config(self)
        Axi4Lite_b._config(self)

    def _declr(self):
        Axi_id._declr(self)
        Axi4Lite_b._declr(self)

    
class Axi4LiteWithId(Axi4Lite):
    """
    Axi4-lite bus interface
    """
    AW_CLS = Axi4Lite_addr_withId
    AR_CLS = Axi4Lite_addr_withId
    W_CLS = Axi4Lite_w_withId
    R_CLS = Axi4Lite_r_withId
    B_CLS = Axi4Lite_b_withId

