from hdl_toolkit.hdlObjects.typeShortcuts import vecT, vec
from hdl_toolkit.interfaces.std import Clk, RdSynced, s
from hdl_toolkit.synthesizer.codeOps import If, c
from hdl_toolkit.synthesizer.interfaceLevel.interface import Interface
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.param import Param, evalParam
from hwtLib.mem.lutRam import RAM64X1S


class CamStorageInIntf(Interface):
    def _config(self):
        self.COLUMNS = Param(1)
        self.ROWS = Param(1)
        
    def _declr(self):
        COLUMNS = self.COLUMNS
        self.addr = s(dtype=vecT(COLUMNS * 6))  # [TODO] this is address actually
        self.dataIn = s(dtype=vecT(COLUMNS))  # [TODO] rename to dataIn
        self.we = s(dtype=vecT(self.ROWS))
       

        
class CamStorage(Unit):
    """
    Cam storage mapped in lutRAMs
    This is matrix like structure of lutRams.
    din port selects address 
    
    """
    def _config(self):
        CamStorageInIntf._config(self)
    
    def _declr(self):
        with self._asExtern():
            self.clk = Clk()
            
            with self._paramsShared():
                self.din = CamStorageInIntf()

            self.match = RdSynced()
            self.match._replaceParam("DATA_WIDTH", self.ROWS)
        
        
        self.rams = []
        for _ in range(evalParam(self.ROWS).val * evalParam(self.COLUMNS).val):
            # 7Series LUTM
            ram = RAM64X1S()
            ram.INIT.set(vec(0, 64))
            self.rams.append(ram)
        self._registerArray("RAM64X1S_inst", self.rams)
            

    def _impl(self):
        carry_t = vecT(self.COLUMNS + 1)
        ROWS = evalParam(self.ROWS).val
        COLUMNS = evalParam(self.COLUMNS).val
        din = self.din

        # cam_storage_gen :
        for y in range(ROWS):
            match_carry = self._sig("match_carry%d" % y, carry_t)
            # cam_storage_row_gen :
            for x in range(COLUMNS):
                ram = self.rams[y * COLUMNS + x]
                base = x * 6

                c(self.clk, ram.wclk)
                for i in range(6):
                    c(din.addr[base + i], getattr(ram, "a%d" % i))
                
                c(din.dataIn[x], ram.d)
                c(din.we[y], ram.we)
                
                # Carry MUX
                nextCarry = match_carry[x + 1]
                If(ram.o,
                   c(match_carry[x], nextCarry)
                ).Else(
                   c(0, nextCarry)
                )
                
            c(self.match.rd, match_carry[0])
            c(match_carry[self.COLUMNS], self.match.data[y])

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = CamStorage()
    u.COLUMNS.set(2)
    u.ROWS.set(3)
    
    print(toRtl(u))
