from hwt.synthesizer.unit import Unit


class BusBridge(Unit):
    """
    Abstract class for bridges between two interface (not necesary different) types

    :ivar ~.s: slave interface of source interface class
    :ivar ~.m: master interface of destination interface class
    """
