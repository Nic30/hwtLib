from hdl_toolkit.hdlObjects.typeShortcuts import hInt
from hdl_toolkit.interfaces.std import VldSynced
from hdl_toolkit.intfLvl import connect, Unit, Param


class InterfaceArraySample(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(8)
        self.LEN = hInt(3)
    
    def _declr(self):
        with self._asExtern(), self._paramsShared():
            self.a = VldSynced(multipliedBy=self.LEN)
            self.b = VldSynced(multipliedBy=self.LEN)
    
    def _impl(self):
        connect(self.a, self.b)


if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    print(toRtl(InterfaceArraySample))

