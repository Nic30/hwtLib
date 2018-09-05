from hwt.synthesizer.unit import Unit


class BusBridge(Unit):
    """
    Abstract class for bridges between bridge interfaces

    :ivar m: master interface of first interface class
    :ivar s: slave interface of second interface class
    """
