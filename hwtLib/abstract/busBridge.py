from hwt.synthesizer.unit import Unit


class BusBridge(Unit):
    """
    Abstract class for bridges between two interface (not necesary different) types

    :ivar m: slave interface of first interface class where master should be connected
    :ivar s: slave interface of second interface class where master slave be connected
    """
