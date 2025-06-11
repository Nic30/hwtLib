#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
An equivalent of `sphinx-build -b html . build`
Used for simple debugger execution for doc build.
"""
import datetime
from multiprocessing import Pool
import multiprocessing
import os
from sphinx.cmd.build import build_main
import sqlite3
import sys
from typing import Optional

from hwt.hwModule import HwModule
from hwtBuildsystem.examples.synthetizeHwModule import buildHwModule, \
    store_vivado_report_in_db, store_quartus_report_in_db, \
    store_yosys_report_in_db
from hwtBuildsystem.quartus.executor import QuartusExecutor
from hwtBuildsystem.quartus.part import IntelPart
from hwtBuildsystem.vivado.executor import VivadoExecutor
from hwtBuildsystem.vivado.part import XilinxPart
from hwtBuildsystem.yosys.executor import YosysExecutor
from hwtBuildsystem.yosys.part import LatticePart
from sphinx_hwt.utils import construct_hwt_obj


sys.path.insert(0, os.path.abspath('../'))
BUILD_REPORT_DB = "hwt_buildreport_database.db"


def createUnitConstructor(absolute_name:str, constructor_fn_name:Optional[str]):

    def createUnit():
        return construct_hwt_obj(absolute_name, constructor_fn_name, HwModule, 'createUnitConstructor')

    return createUnit


def runSynthJob(args):
    platform, (absolute_name, constructor_fn_name) = args
    print(">>>>>>>>>>>>>>>>>>>>>>>> ", args)
    workerCnt = 1
    component_constructor = createUnitConstructor(absolute_name, constructor_fn_name)
    conn = sqlite3.connect(BUILD_REPORT_DB)
    logComunication = True
    try:
        c = conn.cursor()
        project_path = f"tmp/{platform[0]:s}/{absolute_name:s}"
        if constructor_fn_name:
            project_path = os.path.join(project_path, constructor_fn_name)

        tool_tables = {
            'vivado': 'xilinx_vivado_builds',
            'quartus': 'intel_quartus_builds',
            'yosys': 'yosys_builds',
        }

        try:
            c.execute(f"""\
                SELECT component_name FROM {tool_tables[platform[0]]:s}
                WHERE component_name=?""", (absolute_name,))

            if c.fetchone():
                print(f"Already build {absolute_name:s}")
                #return
        except sqlite3.OperationalError:
            # first run, the table needs to be generated first
            pass

        if platform == ('yosys', 'ic40'):
            start = datetime.datetime.now()
            with YosysExecutor(logComunication=logComunication, workerCnt=workerCnt) as executor:
                dut = component_constructor()
                # part = IntelPart("Cyclone V", "5CGXFC7C7F23C8")
                # part = IntelPart("Arria 10", "10AX048H1F34E1HG")
                part = LatticePart('iCE40', 'up5k', 'sg48')
                project = buildHwModule(executor, dut, project_path, part,
                              synthesize=True,
                              implement=False,
                              writeBitstream=False,
                              # openGui=True,
                              )
                name = ".".join([dut.__class__.__module__, dut.__class__.__qualname__])
                store_yosys_report_in_db(c, start, project, name)

        elif platform == ('vivado', 'zynq7000'):
            start = datetime.datetime.now()
            with VivadoExecutor(logComunication=logComunication, workerCnt=workerCnt) as executor:
                dut = component_constructor()
                __pb = XilinxPart
                part = XilinxPart(
                        __pb.Family.kintex7,
                        __pb.Size._160t,
                        __pb.Package.ffg676,
                        __pb.Speedgrade._2)
                project = buildHwModule(executor, dut, project_path, part,
                              synthesize=True,
                              implement=False,
                              writeBitstream=False,
                              # openGui=True,
                              )
                name = ".".join([dut.__class__.__module__, dut.__class__.__qualname__])
                store_vivado_report_in_db(c, start, project, name)

        elif platform == ('quartus', 'arria10'):
            start = datetime.datetime.now()
            with QuartusExecutor(logComunication=logComunication, workerCnt=workerCnt) as executor:
                dut = component_constructor()
                # part = IntelPart("Cyclone V", "5CGXFC7C7F23C8")
                part = IntelPart("Arria 10", "10AX048H1F34E1HG")
                project = buildHwModule(executor, dut, project_path, part,
                              synthesize=True,
                              implement=False,
                              writeBitstream=False,
                              # openGui=True,
                              )
                name = ".".join([dut.__class__.__module__, dut.__class__.__qualname__])
                store_quartus_report_in_db(c, start, project, name)
        else:
            raise ValueError("Unknown platform", platform)
        conn.commit()
    finally:
        conn.close()


def runSynthesisOfAll():
    conn = sqlite3.connect(BUILD_REPORT_DB)
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM builds")
        all_components = sorted(set(c.fetchall()))
        all_platforms = [('yosys', 'ic40'),
                         ('vivado', 'zynq7000'),
                         ('quartus', 'arria10')
                         ]
        jobs = []
        blacklist = [
            (('quartus', 'arria10'), ('hwtLib.amba.axis_comp.fifo_async.Axi4SFifoAsync', '_example_Axi4SFifoAsync')),
            (('quartus', 'arria10'), ('hwtLib.amba.axi_comp.buff_cdc.AxiBuffCdc', '_example_AxiBuffCdc')),
            (('quartus', 'arria10'), ('hwtLib.amba.axis_comp.cdc.Axi4SCdc', 'example_Axi4SCdc')),
            (('quartus', 'arria10'), ('hwtLib.clocking.cdc.CdcPulseGen', None)),
            (('quartus', 'arria10'), ('hwtLib.clocking.vldSynced_cdc.VldSyncedCdc', '_example_VldSyncedCdc')),
            (('quartus', 'arria10'), ('hwtLib.clocking.cdc.Cdc', None)),
            (('quartus', 'arria10'), ('hwtLib.examples.axi.debugbusmonitor.DebugBusMonitorExampleAxi', None)),
            (('quartus', 'arria10'), ('hwtLib.handshaked.cdc.HandshakedCdc', 'example_HandshakedCdc')),
            (('quartus', 'arria10'), ('hwtLib.handshaked.fifoAsync.HsFifoAsync', '_example_HsFifoAsync')),
            (('quartus', 'arria10'), ('hwtLib.mem.fifoAsync.FifoAsync', '_example_FifoAsync')),

            (('yosys', 'ic40'), ('hwtLib.amba.axis_comp.fifo_async.Axi4SFifoAsync', '_example_Axi4SFifoAsync')),
            (('yosys', 'ic40'), ('hwtLib.amba.axi_comp.buff_cdc.AxiBuffCdc', '_example_AxiBuffCdc')),
            (('yosys', 'ic40'), ('hwtLib.amba.axis_comp.cdc.Axi4SCdc', 'example_Axi4SCdc')),
            (('yosys', 'ic40'), ('hwtLib.clocking.cdc.CdcPulseGen', None)),
            (('yosys', 'ic40'), ('hwtLib.clocking.vldSynced_cdc.VldSyncedCdc', '_example_VldSyncedCdc')),
            (('yosys', 'ic40'), ('hwtLib.clocking.cdc.Cdc', None)),
            (('yosys', 'ic40'), ('hwtLib.examples.axi.debugbusmonitor.DebugBusMonitorExampleAxi', None)),
            (('yosys', 'ic40'), ('hwtLib.handshaked.cdc.HandshakedCdc', 'example_HandshakedCdc')),
            (('yosys', 'ic40'), ('hwtLib.handshaked.fifoAsync.HsFifoAsync', '_example_HsFifoAsync')),
            (('yosys', 'ic40'), ('hwtLib.mem.fifoAsync.FifoAsync', '_example_FifoAsync')),

            # Invalid array access.
            (('yosys', 'ic40'), ('hwtLib.examples.mem.ram.SimpleAsyncRam', None)),

            # invalid size of * res
            #(('vivado', 'zynq7000'), ('hwtLib.logic.pid.PidController', None)),
        ]
        for p in all_platforms:
            for c in all_components:
                if (p, c) in blacklist:
                    continue
                jobs.append((p, c))
        # jobs = [
        #     (('yosys', 'ic40'), ("hwtLib.mem.ram.RamSingleClock", None)),
        #      (('quartus', 'arria10'), ("hwtLib.mem.ram.RamSingleClock", None)),
        #      (('vivado', 'zynq7000'), ("hwtLib.mem.ram.RamSingleClock", None)),
        # ]
        with Pool() as p:
            for _ in p.imap_unordered(runSynthJob, jobs):
                pass
        print("All synthesis done")
    finally:
        conn.close()


#runSynthesisOfAll()
build_main(["-b", "html", ".", "_build", "-j", str(multiprocessing.cpu_count())])
