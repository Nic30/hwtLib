from hwtLib.amba.axi4Lite import Axi4Lite_addr, Axi4Lite_w, Axi4Lite_r, \
    Axi4Lite_b, Axi4Lite
from hwtLib.amba.axi_common import Axi_id


class Axi4Lite_addr_withId(Axi4Lite_addr):
    """
    .. hwt-autodoc::
    """

    def hwConfig(self):
        Axi_id.hwConfig(self)
        Axi4Lite_addr.hwConfig(self)

    def hwDeclr(self):
        Axi_id.hwDeclr(self)
        Axi4Lite_addr.hwDeclr(self)


class Axi4Lite_w_withId(Axi4Lite_w):
    """
    .. hwt-autodoc::
    """

    def hwConfig(self):
        Axi_id.hwConfig(self)
        Axi4Lite_w.hwConfig(self)

    def hwDeclr(self):
        Axi_id.hwDeclr(self)
        Axi4Lite_w.hwDeclr(self)


class Axi4Lite_r_withId(Axi4Lite_r):
    """
    .. hwt-autodoc::
    """

    def hwConfig(self):
        Axi_id.hwConfig(self)
        Axi4Lite_r.hwConfig(self)

    def hwDeclr(self):
        Axi_id.hwDeclr(self)
        Axi4Lite_r.hwDeclr(self)


class Axi4Lite_b_withId(Axi4Lite_b):
    """
    .. hwt-autodoc::
    """

    def hwConfig(self):
        Axi_id.hwConfig(self)
        Axi4Lite_b.hwConfig(self)

    def hwDeclr(self):
        Axi_id.hwDeclr(self)
        Axi4Lite_b.hwDeclr(self)


class Axi4LiteWithId(Axi4Lite):
    """
    Axi4-lite bus interface

    .. hwt-autodoc::
    """
    AW_CLS = Axi4Lite_addr_withId
    AR_CLS = Axi4Lite_addr_withId
    W_CLS = Axi4Lite_w_withId
    R_CLS = Axi4Lite_r_withId
    B_CLS = Axi4Lite_b_withId

