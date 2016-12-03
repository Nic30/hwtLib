from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.serializer.constants import SERI_MODE
from hdl_toolkit.synthesizer.interfaceLevel.emptyUnit import EmptyUnit
from hdl_toolkit.synthesizer.shortcuts import toRtl
from hdl_toolkit.hdlObjects.specialValues import DIRECTION

class IOBUF(EmptyUnit):
    """
    Input output buffer which allow you to use external interface of the chip
    
    @attention: we do not wont this in our serialized code 
                because it is part of synthesis tool as well
                thats why we are excluding it from serialization
    """
    _serializerMode = SERI_MODE.EXCLUDE
    
    def _declr(self):
        with self._asExtern():
            self.O = Signal()  # Output (from buffer)
            self.IO = Signal(masterDir=DIRECTION.INOUT)  # Port pin
            self.I = Signal()  # Inuput (to buffer)
            self.T = Signal()  # Tristate control
    

if __name__ == "__main__":
    u = IOBUF()
    u._serializerMode = SERI_MODE.ALWAYS
    print(toRtl(u))