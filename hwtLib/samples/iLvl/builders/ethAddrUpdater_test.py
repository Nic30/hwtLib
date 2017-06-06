from math import ceil

from hwt.bitmask import setBitRange, mask, selectBitRange
from hwt.hdlObjects.constants import Time
from hwt.hdlObjects.frameTemplate import FrameTemplate
from hwt.hdlObjects.transactionTemplate import TransactionTemplate
from hwt.simulator.simTestCase import SimTestCase
from hwt.simulator.types.simBits import simBitsT
from hwtLib.amba.sim.axi3DenseMem import Axi3DenseMem
from hwtLib.samples.iLvl.builders.ethAddrUpdater import EthAddrUpdater, \
    frameHeader
from hwt.hdlObjects.types.bits import Bits
from hwt.hdlObjects.types.struct import HStruct
from hwt.hdlObjects.types.array import Array


def lookupData(part, data):
    raise NotImplementedError()

def _buildFieldToDataDict(dtype, data, res):
    # assert data is None or isinstance(data, dict)
    for f in dtype.fields:
        try:
            fVal = data[f.name]
        except KeyError:
            fVal = None
        
        if isinstance(f.dtype, Bits):
            if fVal is not None:
                assert isinstance(fVal, int)
                res[f] = fVal
        elif isinstance(f.dtype, HStruct):
            if fVal:
                _buildFieldToDataDict(f.dtype, fVal, res)
        elif isinstance(f.dtype, Array):
            if fVal:
                # assert isinstance(fVal, class_or_tuple)
                res[f] = fVal
    
    return res

def buildFieldToDataDict(structT, data):
    return _buildFieldToDataDict(structT, data, {})

def packData(self, structT, data):
    """
    Pack data into list of BitsVal of specified dataWidth

    :param dataWidth: width of word
    :param structT: HStruct type instance
    :param data: list of values for struct fields (with name specified) or dictionary {fieldName: value}

    :return: list of BitsVal which are representing values of words
    """
    typeOfWord = simBitsT(self.wordWidth, None)
    fieldToVal = buildFieldToDataDict(structT, data)
    for i, transactionParts in self.walkWords(showPadding=True):
        actualVldMask = 0
        actualVal = 0
        for tPart in transactionParts:
            high, low = tPart.getBusWordBitRange()
            fhigh, flow = tPart.getFieldBitRange()
            if not tPart.isPadding:
                val = fieldToVal.get(tPart.tmpl.origin, None)
            else:
                val = None

            if val is None:
                newBits = 0
                vld = 0
            else:
                newBits = selectBitRange(val, flow, fhigh - flow)
                vld = mask(high - low) << low

            setBitRange(actualVal, low, high - low, newBits)
            setBitRange(actualVal, low, high - low, vld)
                
        yield typeOfWord.getValueCls()(actualVal, typeOfWord, actualVldMask, -1)



class EthAddrUpdaterTC(SimTestCase):
    def test_simpleOp(self):
        DW = 64
        AW = 32

        u = EthAddrUpdater()
        u.DATA_WIDTH.set(DW)
        u.ADDR_WIDTH.set(AW)
        
        self.prepareUnit(u)
        
        r = self.randomize 
        r(u.axi_m.ar)
        r(u.axi_m.r)
        r(u.axi_m.aw)
        r(u.axi_m.w)
        r(u.axi_m.b)
        
        m = Axi3DenseMem(u.clk, u.axi_m)
        tmpl = TransactionTemplate(frameHeader)
        frameTmpl = list(FrameTemplate.framesFromTransactionTemplate(tmpl, DW))[0]

        def randFrame():  
            rand = self._rand.getrandbits
            data = {"eth":{"src": rand(48), "dst": rand(48)},
                    "ipv4":{"src":rand(32), "dst": rand(32)}}
            ptr = m.calloc(ceil(frameHeader.bit_length() / DW),
                            DW // 8,
                            initValues=list(packData(frameTmpl, frameHeader, data)))
            return ptr, data
        
        framePtr, frameData = randFrame()
        
        u.packetAddr._ag.data.append(framePtr)
        
        self.doSim(1000 * Time.ns)
        
        updatedFrame = m.getStruct(framePtr, frameHeader)
        
        
if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(EthAddrUpdaterTC('test_simpleOp'))
    suite.addTest(unittest.makeSuite(EthAddrUpdaterTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)    
