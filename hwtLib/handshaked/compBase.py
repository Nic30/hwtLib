from typing import Type, Union, Optional, List

from hwt.hwIOs.std import HwIODataRdVld, HwIORdVldSync, HwIOSignal
from hwt.hwParam import HwParam
from hwt.hwModule import HwModule
from hwt.hwIO import HwIO


class HandshakedCompBase(HwModule):
    """
    Abstract class for components which has HwIODataRdVld interface as main
    """

    def __init__(self, hshwIO: Type[HwIORdVldSync],
                 hdl_name_override:Optional[str]=None):
        """
        :param hshwIO: class of interface which should be used
            as interface of this unit
        """
        assert(issubclass(hshwIO, (HwIODataRdVld, HwIORdVldSync))), hshwIO
        self.hwIOCls = hshwIO
        HwModule.__init__(self, hdl_name_override=hdl_name_override)

    def _config(self):
        self.HWIO_CLS = HwParam(self.hwIOCls)
        self.hwIOCls._config(self)

    @classmethod
    def get_valid_signal(cls, hwIO: HwIORdVldSync) -> HwIOSignal:
        return hwIO.vld

    @classmethod
    def get_ready_signal(cls, hwIO: HwIORdVldSync) -> HwIOSignal:
        return hwIO.rd

    def get_data(self, hwIO: HwIORdVldSync) -> List[HwIO]:
        rd = self.get_ready_signal(hwIO)
        vld = self.get_valid_signal(hwIO)
        return [
            cHwIO for cHwIO in hwIO._hwIOs
            if (cHwIO is not rd) and (cHwIO is not vld)
        ]
