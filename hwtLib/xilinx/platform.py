from typing import Optional

from hwt.synthesizer.dummyPlatform import DummyPlatform


class XilinxVivadoPlatform(DummyPlatform):

    def __init__(self, part: Optional[str]=None):
        self.part = part
        super(XilinxVivadoPlatform, self).__init__()
