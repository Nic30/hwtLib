from hwt.simulator.simTestCase import SimTestCase


def axi_randomize_per_channel(tc: SimTestCase, axi):
    if axi.HAS_R:
        tc.randomize(axi.ar)
    if axi.HAS_W:
        tc.randomize(axi.aw)
    if axi.HAS_R:
        tc.randomize(axi.r)
    if axi.HAS_W:
        tc.randomize(axi.w)
        tc.randomize(axi.b)
