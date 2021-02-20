from inspect import isgenerator

from hwtLib.amba.datapump.r import Axi_rDatapump
from hwtLib.amba.datapump.w import Axi_wDatapump
from hwtLib.amba.datapump.interconnect.rStricOrder import RStrictOrderInterconnect
from hwtLib.amba.datapump.interconnect.wStrictOrder import WStrictOrderInterconnect


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
        axi.ar(datapump.axi.ar, exclude=exclude)
        datapump.axi.r(axi.r)

        if isinstance(controller, (list, tuple)):
            interconnect = RStrictOrderInterconnect()
            # @for cntrl, reqIn in zip(controller, req_join.dataIn):
            # @    reqIn(HsBuilder(parent, cntrl.rDatapump.req).reg().end)

            # datapump.driver.req(req_join.dataOut)
        else:
            datapump.driver(controller.rDatapump)
            return

    elif isinstance(datapump, Axi_wDatapump):
        axi.aw(datapump.axi.aw, exclude=exclude)
        # axi3/4 connection
        if not hasattr(axi.w, "id") and hasattr(datapump.axi.w, "id"):
            exclude_ = [datapump.axi.w.id]
        else:
            exclude_ = []
        if exclude:
            exclude_.extend(exclude)

        axi.w(datapump.axi.w, exclude=exclude_)
        datapump.axi.b(axi.b)

        if isinstance(controller, (list, tuple)):
            interconnect = WStrictOrderInterconnect()
        else:
            datapump.driver(controller.wDatapump)
            return

    else:
        raise TypeError(f"Unsupported datapump type {datapump.__class__}")

    interconnect.configureFromDrivers(controller, datapump, byInterfaces=True)
    setattr(parent, datapump._name + "_interconnect", interconnect)
    interconnect.clk(parent.clk)
    interconnect.rst_n(parent.rst_n)
    interconnect.connectDrivers(controller, datapump)
