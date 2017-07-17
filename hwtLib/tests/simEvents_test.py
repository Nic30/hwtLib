from inspect import isfunction
import types
import unittest

from hwt.hdlObjects.constants import Time
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.samples.mem.rom import SimpleRom, SimpleSyncRom
from hwtLib.samples.statements.fsm import FsmExample


class ProcCallWrap():
    def __init__(self, procFn):
        self.procFn = procFn
        self.calls = 0

    def __call__(self, model, sim, io):
        # if sim.now > 0:
        #     print(int(sim.now // 1000), self.procFn.__name__[len("assig_process_"):])
        self.calls += 1
        return self.procFn(model, sim, io)


class SimEventsTC(SimTestCase):
    def mockProcesses(self, unit, modelCls):
        for name in dir(modelCls):
            pFn = getattr(modelCls, name)
            if not name.startswith("assig") or not isfunction(pFn):
                continue

            p = ProcCallWrap(pFn)
            m = types.MethodType(p, modelCls)
            setattr(modelCls, name, m)

    def test_number_of_proc_evaluation_async_rom(self):
        u = SimpleRom()
        self.prepareUnit(u, onAfterToRtl=self.mockProcesses)

        u.addr._ag.data.extend([0, 1, 2, 3, None, 3, 2, 1])

        self.doSim(80 * Time.ns)

        for p in self.model._processes:
            self.assertEqual(p.calls, 8)

    def test_number_of_proc_evaluation_sync_rom(self):
        u = SimpleSyncRom()
        self.prepareUnit(u, onAfterToRtl=self.mockProcesses)

        u.addr._ag.data.extend([0, 1, 2, 3, None, 3, 2, 1])

        self.doSim(90 * Time.ns)
        for p in self.model._processes:
            self.assertEqual(p.calls, 9 + 1, p.procFn)

    def test_number_of_proc_evaluation_fsm(self):
        u = FsmExample()
        self.prepareUnit(u, onAfterToRtl=self.mockProcesses)

        u.a._ag.data.extend([1, 1, 1, 0, 0, 0, 0, 0])
        u.b._ag.data.extend([0, 1, 0, 0, 1, 0, 1, 0])

        self.doSim(80 * Time.ns)

        for p in self.model._processes:
            # st_next will be evaluated after write of agents and after write from st
            self.assertLessEqual(p.calls, 12, p.procFn)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    # suite.addTest(SimEventsTC('test_number_of_proc_evaluation_fsm'))
    suite.addTest(unittest.makeSuite(SimEventsTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)
