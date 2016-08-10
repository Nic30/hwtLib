from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.hdlObjects.types.array import Array
from hdl_toolkit.interfaces.std import Signal, Clk
from hdl_toolkit.synthesizer.codeOps import connect, If
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit


class SimpleRom(Unit):
    def _declr(self):
        with self._asExtern():
            self.addr = Signal(dtype=vecT(2))
            self.dout = Signal(dtype=vecT(8))
        
    def _impl(self):
        rom = self._sig("rom_data", Array(vecT(8), 4), defVal=[1, 2, 3, 4])
        connect(rom[self.addr], self.dout)

class SimpleSyncRom(SimpleRom):
    def _declr(self):
        super()._declr()
        with self._asExtern():
            self.clk = Clk()
    
    def _impl(self):
        rom = self._sig("rom_data", Array(vecT(8), 4), defVal=[1, 2, 3, 4])
        
        If(self.clk._onRisingEdge(),
           connect(rom[self.addr], self.dout)  
        )


if __name__ == "__main__": # alias python main function
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    print(toRtl(SimpleSyncRom))