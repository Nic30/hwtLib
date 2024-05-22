from io import StringIO
from typing import Union

from hwt.hdl.types.array import HArray
from hwt.hdl.types.bitsConst import HBitsConst
from hwt.hdl.types.struct import HStruct
from hwt.simulator.simTestCase import SimTestCase
from hwt.hwIO import HwIO
from hwt.synthesizer.rtlLevel.rtlSignal import RtlSignal
from hwtLib.amba.axi_comp.oooOp.utils import OOOOpPipelineStage
from hwtLib.examples.axi.oooOp.counterHashTable import OooOpExampleCounterHashTable
from hwtSimApi.basic_hdl_simulator.model import BasicRtlSimModel
from hwtSimApi.constants import CLK_PERIOD
from hwtSimApi.triggers import Edge, WaitCombStable
from pyMathBitPrecise.bit_utils import ValidityError


def OutOfOrderCummulativeOp_dump_pipeline(tc: SimTestCase, dut: OooOpExampleCounterHashTable, model: BasicRtlSimModel, states:list):
    m = model.io
    clk = dut.clk
    if clk._sigInside is None:
        clk = clk._sig
    else:
        clk = clk._sigInside
    clk = getattr(m, clk.name)

    def int_or_none(v):
        try:
            return int(v)
        except ValidityError:
            return None

    def read_data(sig: Union[RtlSignal, HwIO]):
        """
        read data from simulation
        """
        if isinstance(sig, HwIO):
            if sig._hwIOs:
                return tuple(read_data(hwIO) for hwIO in sig._hwIOs)
            else:
                sig = sig._sig
        return int_or_none(getattr(m, sig.name).read())
    
    has_operation = hasattr(dut, "OPERATION")
    has_trans_data = dut.TRANSACTION_STATE_T is not None
    has_composite_data = isinstance(dut.MAIN_STATE_T, (HStruct, HArray))
    ops_without_match = []
    if has_operation:
        for n in ("SWAP_BY_ADDR", "READ_BY_ADDR"):
            o = getattr(dut.OPERATION, n, None)
            if o is not None:
                ops_without_match.append(o)
 
    while True:
        yield Edge(clk)
        yield WaitCombStable()

        if clk.read():
            clk_i = tc.hdl_simulator.now // CLK_PERIOD
            cur_state = []
            for st in dut.pipeline:
                st: OOOOpPipelineStage
                vld = read_data(st.valid)
                if vld:
                    if st.index == 0:
                        addr = -1
                        op = -1 if has_operation else None
                    else:
                        addr = read_data(st.addr)
                        assert addr is not None
                    
                    trans_state_present = st.index > 0 and st.index <= dut.PIPELINE_CONFIG.WAIT_FOR_WRITE_ACK
                    if has_operation:
                        if trans_state_present:
                            op = read_data(st.transaction_state.operation)
                            assert op is not None
                        else:
                            op = None
                    
                    if st.index >= dut.PIPELINE_CONFIG.STATE_LOAD and st.index < dut.PIPELINE_CONFIG.WRITE_BACK:
                        if has_trans_data and op not in ops_without_match:
                            key_match = []
                            for hwIO, km in enumerate(st.key_matches):
                                if not isinstance(km, HBitsConst):
                                    km = read_data(km)
                                    assert km is not None, (op, st, hwIO)
                                    if km:
                                        key_match.append(hwIO)
                        else:
                            key_match = None
 
                        collision = None
                        for hwIO, cd in enumerate(st.collision_detect):
                            if not isinstance(cd, int):
                                cd = read_data(cd)
                                assert cd is not None
                                if cd:
                                    collision = hwIO
                                    # assert read_data(u.pipeline[hwIO].valid), (clk_i,
                                    #    u.pipeline[hwIO].valid.name,
                                    #    "not valid and we expecting collision with it")            
                                    break
                            
                    else:
                        key_match = None
                        collision = None

                    if st.index >= dut.PIPELINE_CONFIG.STATE_LOAD and st.index <= dut.PIPELINE_CONFIG.WRITE_BACK:
                        wr_forward = []
                        if st.index == dut.PIPELINE_CONFIG.WRITE_BACK:
                            src_st = dut.pipeline[dut.PIPELINE_CONFIG.WRITE_BACK]
                            if getattr(m, f"write_forwarding_en_{st.index}from{src_st.index}").read():
                                wr_forward.append(src_st.index)
                        else:
                            for src_st in dut.pipeline[dut.PIPELINE_CONFIG.WRITE_BACK:]:
                                if getattr(m, f"write_forwarding_en_{st.index}from{src_st.index}").read():
                                    wr_forward.append(src_st.index)
                    else:
                        wr_forward = None
                    
    
        
                    if has_trans_data:
                        if trans_state_present:
                            orig_d = st.transaction_state.original_data
                            t_item_valid = read_data(orig_d.item_valid)
                            t_key = read_data(orig_d.key)
                            t_data = read_data(orig_d.value)
                        else:
                            t_item_valid = None
                            t_key = None
                            t_data = None

                        t_data = (t_item_valid, t_key, t_data)

                    else:
                        t_data = None

                    if has_composite_data:
                        item_vld = read_data(st.data.item_valid)
                        # assert item_vld is not None
                        if item_vld:
                            key = read_data(st.data.key)
                            data = read_data(st.data.value)
                        else:
                            key = None
                            data = None
                        data = (item_vld, key, data)

                    else:
                        data = read_data(st.data)

                    state_data = (op, addr,
                            t_data,
                            data,
                            collision, wr_forward, key_match)
                else:
                    state_data = None
                
                cur_state.append(state_data)

            if not states or states[-1][1] != cur_state:
                states.append((clk_i, cur_state))  
                # print(f"clk {clk_i}: {cur_state}")
                for st_data in cur_state[dut.PIPELINE_CONFIG.STATE_LOAD:dut.PIPELINE_CONFIG.WRITE_BACK]:
                    if st_data is not None:
                        (_, addr, _, data, collision, wr_forward, _) = st_data
                        if has_composite_data:
                            (item_vld, key, data) = data
                        else:
                            item_vld = 1
                            key = None
                            # data = data

                        for st in dut.pipeline[dut.PIPELINE_CONFIG.WRITE_BACK:(len(dut.pipeline) if collision is None else collision)]:
                            if st.index == collision:
                                assert read_data(st.addr) and read_data(st.addr) == addr, (clk_i,
                                    "collision prediction was invalid", st.index,
                                    read_data(st.valid), read_data(st.addr), addr
                                    )
                            else:
                                if read_data(st.valid):
                                    assert read_data(st.addr) != addr, (clk_i,
                                        "collision prediction missed item", st.index, read_data(st.addr))
        
    
def OutOfOrderCummulativeOp_dump_pipeline_html(file: StringIO, dut: OooOpExampleCounterHashTable, states: list):
    rows = []
    st_names = {getattr(dut.PIPELINE_CONFIG, n): n for n in [
                    "READ_DATA_RECEIVE",
                    "STATE_LOAD",
                    "WRITE_BACK",
                    "WAIT_FOR_WRITE_ACK"]}
    if hasattr(dut, "OPERATION"):
        operation_names = {}
        for attr in dir(dut.OPERATION):
            v = getattr(dut.OPERATION, attr)
            if isinstance(v, int):
                assert v not in operation_names, (attr, v, operation_names)
                operation_names[v] = attr
    else:
        operation_names = None
    has_trans_data = dut.TRANSACTION_STATE_T is not None
    has_composite_data = isinstance(dut.MAIN_STATE_T, (HStruct, HArray))

    for clk_i, total_st in states:
        if not rows:
            # construct header
            state_cells = []
            for i in range(len(total_st)):
                st_name = st_names.get(i, None)
                if st_name is None:
                    state_cells.append(f"<th>{i:d}</th>")
                else:
                    state_cells.append(f"<th>{i:d} {st_name:s}</th>")
            state_cells = "".join(state_cells)
            row = f"<tr><th></th>{state_cells:s}</tr>"
            rows.append(row)
        
        state_cells = []
        for st_i, st in enumerate(total_st):
            if st is None:
                cell = f"<td></td>" 
            else:
                (op, addr,
                 t,
                 data,
                 collision, wr_forward, key_match) = st
                if st_i == 0 or st_i > dut.PIPELINE_CONFIG.WAIT_FOR_WRITE_ACK:
                    op = ""  # operation is not present in these stages
                    t = None
                else:
                    if operation_names is None:
                        assert op is None
                    else:
                        op = operation_names.get(op, "INVALID")

                    if has_trans_data:
                        (t_item_valid, t_key, t_data) = t
                        if t_item_valid is None:
                            t = ""
                        else:
                            t = repr((t_item_valid, t_key, t_data))
                    else:
                        t = None

                if has_composite_data:
                    (item_vld, key, data) = data
                    if item_vld:
                        d = repr((item_vld, key, data))
                    elif item_vld is None:
                        d = "INVALID"
                    else:
                        d = ""
                else:
                    d = repr(data)
                    
                cell_lines = []
                if st_i > 0:
                    if operation_names is not None:
                        cell_lines.append(f"0x{addr:x} {op:s}<br/>")
                    else:
                        cell_lines.append(f"0x{addr:x}<br/>")
                
                if t is not None:
                    cell_lines.append(f"t:{t}<br/>")
                cell_lines.append(f"d:{d}<br/>")
                if collision is not None:
                    cell_lines.append(f"collision:{collision}<br/>")
                if wr_forward is not None:
                    cell_lines.append(f"wr_forward:{wr_forward}<br/>")
                    
                if key_match is not None:
                    cell_lines.append(f"t_key_match:{key_match}<br/>")

                cell_lines = "".join(cell_lines)
                if st_i >= dut.PIPELINE_CONFIG.WRITE_BACK: 
                    style =  ' style="background-color:LightGreen;"'
                else:
                    style = ''

                cell = f"<td{style:s}>{cell_lines:s}</td>" 
                    
            state_cells.append(cell)   
        
        state_cells = "".join(state_cells)
        row = f"<tr><td>{clk_i}</td>{state_cells:s}</tr>"
        rows.append(row)

    rows = "\n".join(rows)
    file.write(f"<!DOCTYPE html><html><head><meta charset='utf-8'/></head><body><table border='1'>\n{rows}\n</table></body></html>\n")
