from hwt.hwIOs.agents.rdVldSync import HwIODataRdVldAgent


class BaseAxiAgent(HwIODataRdVldAgent):

    @classmethod
    def get_ready_signal(cls, hwIO):
        return hwIO.ready._sigInside

    @classmethod
    def get_valid_signal(cls, hwIO):
        return hwIO.valid._sigInside
