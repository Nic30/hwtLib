from typing import Optional, List

from hwt.serializer.combLoopAnalyzer import CombLoopAnalyzer
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.constants import RESP_OKAY
from hwtLib.examples.errors.combLoops import freeze_set_of_sets
from pyMathBitPrecise.bit_utils import mask, get_bit_range, get_bit


class Axi_datapumpTC(SimTestCase):

    def aTrans(self, addr, _len, _id):
        axi = self.u.axi
        if axi.HAS_R:
            axi_a = axi.ar
        else:
            axi_a = axi.aw

        if axi.LEN_WIDTH:
            return axi_a._ag.create_addr_req(addr, _len, _id=_id)
        else:
            return axi_a._ag.create_addr_req(addr)

    def test_no_comb_loops(self):
        s = CombLoopAnalyzer()
        s.visit_Unit(self.u)
        comb_loops = freeze_set_of_sets(s.report())
        # for loop in comb_loops:
        #     print(10 * "-")
        #     for s in loop:
        #         print(s.resolve()[1:])

        self.assertEqual(comb_loops, frozenset())

    def mkReq(self, addr, _len, rem=0, _id=0):
        if self.LEN_MAX_VAL:
            return (addr, _len, rem)
        else:
            assert _len == 0, _len
            return (addr, rem)

    def rTrans(self, data, _id=0, resp=RESP_OKAY, last=True):
        return (_id, data, resp, int(last))

    def rDriverTrans(self, data, last, strb=mask(64 // 8), id_=0):
        return (data, strb, int(last))

    def spotReadMemcpyTransactions(self,
                               base: int,
                               len_: int,
                               singleReqFrameLen: Optional[int],
                               data:List[int]=None,
                               addData: bool=True,
                               lastWordByteCnt=None):
        """
        :param base: base address where to start
        :param len_: total number of words to copy - 1
        :param singleReqFrameLen: total max number of words in a single frame - 1
        :param addData: if True transactions for data channels are prepared as well
        :param lastWordByteCnt: if not None it is used to generate a strb (byte enable mask) in last
            word of reference receive data
        """
        u = self.u
        addr_step = u.DATA_WIDTH // 8
        req = u.driver._ag.req

        assert base % addr_step == 0, base
        MAGIC = 100
        if singleReqFrameLen is None:
            singleReqFrameLen = u.driver.req.MAX_LEN

        if lastWordByteCnt is None:
            lastWordByteCnt = 0
        else:
            assert lastWordByteCnt > 0 and lastWordByteCnt <= addr_step, lastWordByteCnt
            lastWordByteCnt %= addr_step

        AXI_LEN_MAX = min(2 ** u.axi.LEN_WIDTH, singleReqFrameLen + 1, len_ + 1)

        offset = base
        end = offset + (len_ + 1) * addr_step
        while offset < end:
            if offset != base and lastWordByteCnt != 0:
                raise NotImplementedError()
            len__ = min(singleReqFrameLen, (end - offset) // addr_step - 1)
            req.data.append(self.mkReq(offset, len__, rem=lastWordByteCnt))
            offset += addr_step * (singleReqFrameLen + 1)

        offset = base
        end = offset + (len_ + 1) * addr_step
        ar_ref = []
        while offset < end:
            len__ = min(AXI_LEN_MAX, (end - offset) // addr_step) - 1
            a = self.aTrans(
                offset,
                len__,
                0
            )
            ar_ref.append(a)
            offset += addr_step * AXI_LEN_MAX

        rIn = u.axi.r._ag.data
        r_ref = []
        M_ALL = mask(addr_step)
        if addData:
            if data is not None:
                assert len(data) == len_ + 1, (len_ + 1, data)
            for i in range(len_ + 1):
                lastForDriver = (i + 1) % (singleReqFrameLen + 1) == 0 or i == len_
                lastForAxi = (i + 1) % AXI_LEN_MAX == 0
                last = lastForDriver or lastForAxi
                if data is not None:
                    d = data[i]
                else:
                    d = MAGIC + base + i

                rIn.append(self.rTrans(d, last=last))
                if lastForDriver and lastWordByteCnt != 0:
                    m = mask(lastWordByteCnt)
                else:
                    m = M_ALL

                r_ref.append(self.rDriverTrans(d, int(lastForDriver), m))
        else:
            assert not data

        return ar_ref, r_ref

    def check_r_trans(self, ar_ref, driver_r_ref):
        u = self.u

        self.assertEqual(len(u.driver._ag.req.data), 0)
        self.assertEqual(len(u.axi.r._ag.data), 0)

        r_data = []
        m_width = u.driver.r.strb._dtype.bit_length()
        for (d, m, l) in u.driver.r._ag.data:
            if l:
                m = int(m)
                invalid_seen = False
                for B_i in range(m_width):
                    B = get_bit_range(d.vld_mask, B_i * 8, 8)
                    _m = get_bit(m, B_i)
                    if _m and B != 0xff:
                        d = None
                        break
                    if invalid_seen:
                        if _m:
                            raise ValueError("The value prefix is invalid, but there is a part of the value which is valid", d, B_i)
                    else:
                        if not _m:
                            invalid_seen = True

                if d is not None:
                    # mask removes the potentially invalid bytes
                    d = d.val
            r_data.append((d, m, l))

        self.assertValSequenceEqual(r_data, driver_r_ref)

        self.assertValSequenceEqual(u.axi.ar._ag.data, ar_ref)
