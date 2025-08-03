from typing import Optional, Union

from hwt.hObjList import HObjList
from hwt.hdl.types.bits import HBits
from hwt.hwIO import HwIO
from hwt.hwModule import HwModule
from hwt.synthesizer.interfaceLevel.getDefaultClkRts import getClk, getRst
from hwt.synthesizer.interfaceLevel.hwModuleImplHelpers import getSignalName


class AbstractComponentBuilder(object):
    """
    Helper class which simplifies instantiation of commonly used components
    with configuration based on input/output interface

    :ivar ~.parent: unit in which will be all units created by this builder instantiated
    :ivar ~.compId: last component sequential number, used to avoid name collisions
    :ivar ~.lastComp: last builded component
    :ivar ~.end: last interface of data-path
    :ivar ~.name: prefix for all instantiated units
    :attention: input port is taken from self.end
    """

    def __init__(self, parent: HwModule, srcInterface: Union[HwIO, HObjList], name: Optional[str]=None, master_to_slave:bool=True):
        """
        :param parent: HwModule where all submodules created by this builder will be instantiated
        :param name: prefix for all instantiated units
        :param srcInterface: start of data-path
        :param master_to_slave: if True the circuit is build in natural direction
            (master to slave, input to output) othervise it is build in reverse direction
        """
        self.parent = parent
        self.lastComp = None
        self.end = srcInterface
        if name is None:
            assert srcInterface is not None
            name = "gen_" + getSignalName(srcInterface)

        self.name = name
        self.master_to_slave = master_to_slave
        self.compId = 0

    def getClk(self):
        """
        lookup clock signal on parent
        """
        end = self.end
        if end is None:
            return getClk(self.parent)
        else:
            return end._getAssociatedClk()

    def getRstn(self):
        """
        lookup reset(n) signal on parent
        """
        end = self.end
        if end is None:
            rst = getRst(self.parent)
        else:
            rst = end._getAssociatedRst()

        if isinstance(rst._dtype, HBits) and rst._dtype.negated:
            return rst
        else:
            return ~rst

    def getHwIOCls(self):
        """
        Get class of interface which this builder is currently using.
        """
        return self._getHwIOCls(self.end)

    def _getHwIOCls(self, hwIO: Union[HwIO, HObjList]):
        """
        Get real HwIO class of interface
        """
        if isinstance(hwIO, HObjList):
            return self._getHwIOCls(hwIO[0])

        return hwIO.__class__

    def _findSuitableName(self, name: str, firstWithoutCntrSuffix=False):
        """
        Find a suitable name for component (= name without collisions), add suffix with counter to solve name collisions
        
        :param firstWithoutCntrSuffix: if True name is used as is if possible if False counter suffix is always added
        """
        if self.name:
            namePrefix = f"{self.name:s}_"
        else:
            namePrefix = ""
        
        if firstWithoutCntrSuffix:
            _name = f"{namePrefix:s}{name:s}"
            try:
                getattr(self.parent, _name)
            except AttributeError:
                return _name

        while True:
            _name = f"{namePrefix:s}{name:s}_{self.compId:d}"
            try:
                getattr(self.parent, _name)
            except AttributeError:
                return _name
                break
            self.compId += 1

        self.compId += 1

    def _propagateClkRstn(self, m: HwModule):
        """
        Connect clock and reset to HwModule "m"
        """
        if hasattr(m, "clk"):
            m.clk(self.getClk())

        if hasattr(m, 'rst_n'):
            m.rst_n(self.getRstn())

        if hasattr(m, "rst"):
            m.rst(~self.getRstn())
