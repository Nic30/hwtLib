#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from copy import copy

from hwt.serializer.combLoopAnalyzer import CombLoopAnalyzer
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axiLite_comp.sim.utils import axi_randomize_per_channel
from hwtLib.amba.axi_comp.oooOp.examples.counterHashTable import OooOpExampleCounterHashTable
from hwtLib.amba.axi_comp.sim.ram import AxiSimRam
from hwtLib.examples.errors.combLoops import freeze_set_of_sets
from hwtSimApi.constants import CLK_PERIOD


def MState(key, data):
    return (int(key is not None), key, data)


def TState(key, data, operation, match=0, reset=0):
    return (
        reset,
        MState(key, data),
        match,
        operation
    )


def in_trans(addr, reset, key, data, match, operation):
    return (
        addr,
        TState(key, data, operation, match, reset),
    )


OP = OooOpExampleCounterHashTable.OPERATION


class OooOpExampleCounterHashTable_TC(SimTestCase):

    @classmethod
    def setUpClass(cls):
        u = cls.u = OooOpExampleCounterHashTable()
        # MAIN_STATE_T = HStruct(
        #     (BIT, "item_valid"),
        #     (Bits(32), "key"),
        #     (Bits(self.DATA_WIDTH - 32 - 1), "value"),
        # )
        # # the transaction always just increments the counter
        # # so there is no need for transaction state
        # TRANSACTION_STATE_T = HStruct(
        #     # if true the key was modified during processing
        #     # and we need to recirculate the transaction in pipeline
        #     # (which should be done by parent component and it does not happen automatically)
        #     (BIT, "reset"),
        #     (self.MAIN_STATE_T, "data"),
        #     # for output 1 if key was same as key in lookup transaction
        #     (BIT, "key_match"),
        #     (Bits(2), "operation"), # :see: :class:`~.OPERATION`
        # )

        u.ID_WIDTH = 2
        u.ADDR_WIDTH = u.ID_WIDTH  + 3
        cls.compileSim(u)

    def setUp(self):
        SimTestCase.setUp(self)
        u = self.u
        self.m = AxiSimRam(axi=u.m)

    def test_nop(self):
        u = self.u

        self.runSim(10 * CLK_PERIOD)
        self.assertEmpty(u.dataOut._ag.data)
        self.assertEmpty(u.m.aw._ag.data)
        self.assertEmpty(u.m.w._ag.data)
        self.assertEmpty(u.m.ar._ag.data)

    def _test_incr(self, inputs, randomize=False, mem_init={}):
        u = self.u
        ADDR_ITEM_STEP = 2 **  u.ADDR_OFFSET_W
        for i in range(2 ** u.ADDR_WIDTH // ADDR_ITEM_STEP):
            v = mem_init.get(i, 0)
            if v != 0:
                item_valid, key, value = v
                v = u.MAIN_STATE_T.from_py({"item_valid": item_valid, "key": key, "value": value})
                v = v._reinterpret_cast(u.m.w.data._dtype)
            self.m.data[i] = v

        u.dataIn._ag.data.extend(inputs)

        t = (40 + len(inputs) * 3) * CLK_PERIOD
        if randomize:
            axi_randomize_per_channel(self, u.m)
            self.randomize(u.dataIn)
            self.randomize(u.dataOut)
            t *= 5

        self.runSim(t)

        # check if pipeline registers are empty
        for i in range(u.PIPELINE_CONFIG.WAIT_FOR_WRITE_ACK):
            valid = getattr(self.rtl_simulator.model.io, f"st{i:d}_valid")
            self.assertValEqual(valid.read(), 0, i)

        # check if main state fifo is empty
        ooo_fifo = self.rtl_simulator.model.ooo_fifo_inst.io
        self.assertValEqual(ooo_fifo.item_valid.read(), 0)
        self.assertValEqual(ooo_fifo.read_wait.read(), 1)

        # check if all transactions on AXI are finished
        self.assertEmpty(u.m.b._ag.data)
        self.assertEmpty(u.m.r._ag.data)

        # check output data itself
        dout = u.dataOut._ag.data
        mem = copy(mem_init)
        for _in, _out in zip(inputs, dout):
            (
                addr,
                (
                    reset,
                    (key_vld, key, data),
                    _,
                    operation
                )
            ) = _in
            (
                o_addr,
                (o_found_key_vld, o_found_key, o_found_data),
                (
                    o_reset,
                    (o_key_vld, o_key, o_data),
                    o_match,
                    o_operation
                ),
            ) = _out
            # None or tuple(item_valid, key, data)
            cur = mem.get(addr, None)
            aeq = self.assertValEqual
            aeq(o_addr, addr)
            if operation == OP.LOOKUP:
                # lookup and increment if found
                if cur is not None and cur[0] and int(cur[1]) == key:
                    # lookup sucess
                    aeq(o_reset, 0)
                    aeq(o_match, 1)
                    aeq(o_found_key_vld, 1)
                    aeq(o_found_key, key)
                    aeq(o_found_data, cur[2] + 1)
                    aeq(o_found_key_vld, 1)

                    mem[addr] = (1, key, int(o_found_data))

                else:
                    # lookup fail
                    aeq(o_reset, 0)
                    aeq(o_match, 0)
                    # key remained same
                    aeq(o_key_vld, key_vld)
                    aeq(o_key, key)
                    aeq(o_data, data)
                    # there was nothing so nothig should have been found
                    aeq(o_found_key_vld, int(cur is not None and cur[0]))

            elif operation == OP.LOOKUP_OR_SWAP:
                # lookup and increment or swap if not found
                if cur is not None and cur[0] and int(cur[1]) == key:
                    # lookup sucess
                    aeq(o_reset, 0)
                    aeq(o_match, 1)
                    aeq(o_found_key_vld, 1)
                    aeq(o_found_key, key)
                    aeq(o_found_data, cur[2] + 1)
                    aeq(o_found_key_vld, 1)
                    mem[addr] = (1, key, int(o_found_data))
                else:
                    # swap
                    raise NotImplementedError()
            elif operation == OP.SWAP:
                # swap no matter if the key was found or not, do not increment
                raise NotImplementedError()
            else:
                raise ValueError(operation)

            self.assertValEqual(o_operation, operation)

        self.assertEqual(len(dout), len(inputs))
        # for i in sorted(set(inputs)):
        #    self.assertValEqual(self.m.data[i], inputs.count(i), i)
        for i in range(2 ** u.ADDR_WIDTH // ADDR_ITEM_STEP):
            v = self.m.getStruct(i * ADDR_ITEM_STEP, u.MAIN_STATE_T)
            ref_v = mem.get(i, None)
            if ref_v is None or not ref_v[0]:
                aeq(v.item_valid, 0)
            else:
                aeq(v.item_valid, 1)
                aeq(v.key, ref_v[1])
                aeq(v.value, ref_v[2])

    def test_1x_not_found(self):
        self._test_incr([(0, TState(0, None, OP.LOOKUP)), ])

    def test_r_100x_not_found(self):
        index_pool = list(range(2 ** self.u.ID_WIDTH))
        self._test_incr([
            (self._rand.choice(index_pool), TState(0, None, OP.LOOKUP))
            for _ in range(100)
        ])

    def test_1x_lookup_found(self):
        self._test_incr([(1, TState(99, None, OP.LOOKUP)), ], mem_init={1: MState(99, 20)})

    def test_r_100x_lookup_found(self):
        item_pool = [(i, MState(i + 1, 20 + i)) for i in range(2 ** self.u.ID_WIDTH)]

        self._test_incr(
            [(i, TState(v[1], None, OP.LOOKUP)) for i, v in [
                    self._rand.choice(item_pool) for _ in range(100)
                ]
            ],
            mem_init={i: v for i, v in item_pool}
        )

    def test_r_100x_lookup_found_not_found_mix(self):
        N = 100
        max_id = 2 ** self.u.ID_WIDTH
        item_pool = [(i % max_id, MState(i + 1, 20 + i)) for i in range(max_id * 2)]

        self._test_incr(
            [(i, TState(v[1], None, OP.LOOKUP)) for i, v in [
                    self._rand.choice(item_pool) for _ in range(N)
                ]
            ],
            # :attention: i is modulo mapped that means that
            #     mem_init actually contains only last "n" items from item_pool
            mem_init={i: v for i, v in item_pool}
        )

    def test_1x_lookup_or_swap_found(self):
        self._test_incr(
            [(1, TState(99, None, OP.LOOKUP_OR_SWAP)), ],
            mem_init={1: MState(99, 20)}
        )

    def test_no_comb_loops(self):
        s = CombLoopAnalyzer()
        s.visit_Unit(self.u)
        comb_loops = freeze_set_of_sets(s.report())
        # for loop in comb_loops:
        #     print(10 * "-")
        #     for s in loop:
        #         print(s.resolve()[1:])

        self.assertEqual(comb_loops, frozenset())


if __name__ == "__main__":
    import unittest
    suite = unittest.TestSuite()
    #suite.addTest(OooOpExampleCounterHashTable_TC('test_r_100x_lookup_found_not_found_mix'))
    suite.addTest(unittest.makeSuite(OooOpExampleCounterHashTable_TC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
