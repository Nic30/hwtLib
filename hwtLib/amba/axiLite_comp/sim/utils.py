from hwt.simulator.simTestCase import SimTestCase


def axi_randomize_per_channel(tc: SimTestCase, axi):
    tc.randomize(axi.ar)
    tc.randomize(axi.aw)
    tc.randomize(axi.r)
    tc.randomize(axi.w)
    tc.randomize(axi.b)
