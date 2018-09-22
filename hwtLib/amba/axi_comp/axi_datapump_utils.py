from inspect import isgenerator

from hwt.code import connect
from hwtLib.amba.axi_comp.axi4_rDatapump import Axi_rDatapump
from hwtLib.amba.axi_comp.axi4_wDatapump import Axi_wDatapump
from hwtLib.amba.interconnect.rStricOrder import RStrictOrderInterconnect
from hwtLib.amba.interconnect.wStrictOrder import WStrictOrderInterconnect


def connectDp(parent, controller, datapump, axi, exclude=None):
    """
    Connect datapump with it's controller(s) and axi

    :param controller: (controller compatible with Axi_wDatapump or Axi_rDatapump)
                        or list/tuple/generator of them

    :param datapump: Axi_wDatapump or Axi_rDatapump

    :param axi: axi(3/4) interface which datapump should use
    """
    if isgenerator(controller):
        controller = list(controller)

    if isinstance(controller, (list, tuple)) and len(controller) == 1:
        controller = controller[0]

    if isinstance(datapump, Axi_rDatapump):
        connect(datapump.a, axi.ar, exclude=exclude)
        datapump.r(axi.r)

        if isinstance(controller, (list, tuple)):
            interconnect = RStrictOrderInterconnect()
            # @for cntrl, reqIn in zip(controller, req_join.dataIn):
            # @    reqIn(HsBuilder(parent, cntrl.rDatapump.req).reg().end)

            # datapump.driver.req(req_join.dataOut)
        else:
            datapump.driver(controller.rDatapump)
            return

    elif isinstance(datapump, Axi_wDatapump):
        connect(datapump.a, axi.aw, exclude=exclude)
        # axi3/4 connection
        if not hasattr(axi.w, "id") and hasattr(datapump.w, "id"):
            exclude_ = [datapump.w.id]
        else:
            exclude_ = []
        if exclude:
            exclude_.extend(exclude)

        connect(datapump.w, axi.w, exclude=exclude_)
        datapump.b(axi.b)

        if isinstance(controller, (list, tuple)):
            interconnect = WStrictOrderInterconnect()
        else:
            datapump.driver(controller.wDatapump)
            return

    else:
        raise TypeError("Unsupported datapump type %r" % (datapump.__class__))

    interconnect.configureFromDrivers(controller, datapump, byInterfaces=True)
    setattr(parent, datapump._name + "_interconnect", interconnect)
    interconnect.clk(parent.clk)
    interconnect.rst_n(parent.rst_n)
    interconnect.connectDrivers(controller, datapump)
