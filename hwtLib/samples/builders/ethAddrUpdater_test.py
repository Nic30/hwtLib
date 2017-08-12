from math import ceil

from hwt.hdlObjects.constants import Time
from hwt.hdlObjects.frameTemplate import FrameTemplate
from hwt.hdlObjects.transTmpl import TransTmpl
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.sim.axi3DenseMem import Axi3DenseMem
from hwtLib.samples.builders.ethAddrUpdater import EthAddrUpdater, \
    frameHeader


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
        tmpl = TransTmpl(frameHeader)
        frameTmpl = list(FrameTemplate.framesFromTransTmpl(tmpl, DW))[0]

        def randFrame():
            rand = self._rand.getrandbits
            data = {"eth": {"src": rand(48),
                            "dst": rand(48)
                            },
                    "ipv4": {"src": rand(32),
                             "dst": rand(32)
                            }
                    }
            d = list(frameTmpl.packData(data))
            ptr = m.calloc(ceil(frameHeader.bit_length() / DW),
                           DW // 8,
                           initValues=d)
            return ptr, data

        framePtr, frameData = randFrame()

        u.packetAddr._ag.data.append(framePtr)

        self.doSim(1000 * Time.ns)
        updatedFrame = m.getStruct(framePtr, tmpl)
        self.assertValEqual(updatedFrame.eth.src, frameData["eth"]['dst'])
        self.assertValEqual(updatedFrame.eth.dst, frameData["eth"]['src'])
        self.assertValEqual(updatedFrame.ipv4.src, frameData["ipv4"]['dst'])
        self.assertValEqual(updatedFrame.ipv4.dst, frameData["ipv4"]['src'])


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    # suite.addTest(EthAddrUpdaterTC('test_simpleOp'))
    suite.addTest(unittest.makeSuite(EthAddrUpdaterTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
