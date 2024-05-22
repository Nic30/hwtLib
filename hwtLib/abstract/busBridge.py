from hwt.hwModule import HwModule


class BusBridge(HwModule):
    """
    Abstract class for bridges between two interface (not necessary different) types

    :ivar ~.s: slave interface of source HwIO class
    :ivar ~.m: master interface of destination HwIO class
    """
