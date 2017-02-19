from hwt.code import Concat, If, log2ceil, ForEach
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import VldSynced, Handshaked, Signal
from hwt.interfaces.utils import addClkRstn
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import evalParam, Param
from hwtLib.amba.axiDatapumpIntf import AddrSizeHs
from hwtLib.amba.axis import AxiStream_withId
from hwtLib.handshaked.streamNode import streamSync
from hwtLib.structManipulators.structUtils import StructFieldInfo, \
    StructBusBurstInfo


def createInterface(fInfo):
    i = VldSynced()
    i.DATA_WIDTH.set(fInfo.type.bit_length()) 
    fInfo.interface = i   
    return i

class StructReader(Unit):
    """
    This unit downloads required structure fields
    MAX_DUMMY_WORDS specifies maximum dummy bus words between fields if there is more of ignored space transaction will be split to  
    @attention: interfaces of field will not send data in same time
    """
    def __init__(self, structTemplate):
        """
        example of structTemplate:
        
        [(uint64_t, "item0"), # tuples (type, name) where type has to be instance of Bits type
         (uint64_t, None),    # name = None means this field will be ignored  
         (uint64_t, "item1"),
        ]
        
        * this unit will have item0, item1 interfaces to collect results
        """
        super(StructReader, self).__init__()
        self._structTemplate = structTemplate
    
    def _config(self):
        self.ID = Param(0)
        self.MAX_DUMMY_WORDS = Param(1)
        AddrSizeHs._config(self)
        
    def declareFieldInterfaces(self):
        """
        Declare interfaces for struct fields and collect StructFieldInfo for each field
        """
        structInfo = []
        busDataWidth = evalParam(self.DATA_WIDTH).val
        startBitIndex = 0
        for t, name in self._structTemplate:
            if name is not None:
                info = StructFieldInfo(t, name) 
                startBitIndex = info.discoverFieldParts(busDataWidth, startBitIndex)
                i = createInterface(info)
                
                setattr(self, name, i) 
                structInfo.append(info)
            else:
                startBitIndex += t.bit_length()

        return structInfo
        
        
    def _declr(self):
        addClkRstn(self)
        
        structInfo = self.declareFieldInterfaces()
        self._busBurstInfo = StructBusBurstInfo.packFieldInfosToBusBurst(
                                    structInfo,
                                    evalParam(self.MAX_DUMMY_WORDS).val,
                                    evalParam(self.DATA_WIDTH).val // 8)
        
        self.get = Handshaked()  # data signal is addr of structure to download 
        self.get._replaceParam("DATA_WIDTH", self.ADDR_WIDTH)
                
        with self._paramsShared():
            # interface for communication with datapump
            self.req = AddrSizeHs()
            self.req.MAX_LEN.set(StructBusBurstInfo.sumOfWords(self._busBurstInfo))
            self.r = AxiStream_withId()
        
        self.ack = Signal()  # ready signal form consumer of data from this unit
    
    def _impl(self):
        maxWordIndex = StructBusBurstInfo.sumOfWords(self._busBurstInfo)
        wordIndex = self._reg("wordIndex", vecT(log2ceil(maxWordIndex + 1)), 0)
        
        r = self.r
        req = self.req
        
        req.id ** self.ID
        req.rem ** 0
        
        def f(burst):
            return [ req.addr ** (self.get.data + burst.addrOffset),
                     req.len ** (burst.wordCnt() - 1),
            ]    
        ForEach(self, self._busBurstInfo, f, ack=req.rd)

        streamSync(masters=[self.get], slaves=[req])
            
        
        busVld = self._sig("busVld")    
        busVld ** (r.valid & r.id._eq(self.ID))
        r.ready ** self.ack
        
        for burstInfo in self._busBurstInfo:
            for fieldInfo in burstInfo.fieldInfos:
                lastPart = fieldInfo.parts[-1]
                signalsOfParts = []
                
                for i, part in enumerate(fieldInfo.parts):
                    dataVld = busVld & wordIndex._eq(part.wordIndex)
                    fPartSig = part.getSignal(r.data)
    
                    if part is lastPart:
                        signalsOfParts.append(fPartSig)
                        fieldInfo.interface.data ** Concat(*signalsOfParts)
                        fieldInfo.interface.vld ** dataVld
                        
                    else:
                        if part.wordIndex < lastPart.wordIndex:
                            # part is in some word before last, we have to store its value to reg till the last part arrive
                            fPartReg = self._reg("%s_part_%d" % (fieldInfo.name, i), fPartSig._dtype)
                            If(dataVld,
                               fPartReg ** fPartSig
                            ) 
                            signalsOfParts.append(fPartReg)
                        else:
                            # part is in same word as last so we can take it directly
                            signalsOfParts.append(fPartSig)
            
        If(busVld,
            If(r.last,
               wordIndex ** 0
            ).Else(
                wordIndex ** (wordIndex + 1)
            )
        )        

if __name__ == "__main__":
    from hwtLib.types.ctypes import uint16_t, uint32_t, uint64_t
    from hwt.synthesizer.shortcuts import toRtl
    
    s = [
        (uint64_t, "item0"),  # tuples (type, name) where type has to be instance of Bits type
        (uint64_t, None),  # name = None means this field will be ignored  
        (uint64_t, "item1"),
        (uint64_t, None),
        (uint16_t, "item2"),
        (uint16_t, "item3"),
        (uint32_t, "item4"),
        
        
        (uint32_t, None),
        (uint64_t, "item5"),  # this word is split on two bus words 
        (uint32_t, None),
        
        (uint64_t, None),
        (uint64_t, None),
        (uint64_t, None),
        (uint64_t, "item6"),
        (uint64_t, "item7"),
        
        ]
    u = StructReader(s)
    print(toRtl(u))
