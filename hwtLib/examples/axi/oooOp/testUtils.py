from io import StringIO

from hwt.hdl.types.bitsVal import BitsVal
from hwt.simulator.simTestCase import SimTestCase
from hwtLib.amba.axi_comp.oooOp.utils import OOOOpPipelineStage
from hwtLib.examples.axi.oooOp.counterHashTable import OooOpExampleCounterHashTable
from hwtSimApi.constants import CLK_PERIOD
from hwtSimApi.triggers import Edge, WaitCombStable
from pyMathBitPrecise.bit_utils import ValidityError


def OutOfOrderCummulativeOp_dump_pipeline(tc: SimTestCase, u: OooOpExampleCounterHashTable, states:list):
    clk = u.clk._sigInside
    m = tc.rtl_simulator.model.io

    def int_or_none(v):
        try:
            return int(v)
        except ValidityError:
            return None

    while True:
        yield Edge(clk)
        yield WaitCombStable()

        if clk.read():
            cur_state = []
            for st in u.pipeline:
                st: OOOOpPipelineStage
                vld = getattr(m, st.valid.name).read()
                if vld:
                    if st.index == 0:
                        addr = -1
                        op = -1
                    else:
                        addr = getattr(m, st.addr.name).read()
                        addr = int(addr)
                    
                    if st.index >= u.PIPELINE_CONFIG.STATE_LOAD and st.index < u.PIPELINE_CONFIG.WRITE_BACK:
                        key_match = []
                        for i, km in enumerate(st.key_matches):
                            if not isinstance(km, BitsVal):
                                km = int(getattr(m, km.name).read())
                                if km:
                                    key_match.append(i)
                            
                        collision = None
                        for i, cd in enumerate(st.collision_detect):
                            if not isinstance(cd, int):
                                cd = int(getattr(m, cd.name).read())
                                if cd:
                                    collision = i
                                    assert getattr(m, u.pipeline[i].valid.name).read(), (u.pipeline[i].valid.name, "not valid when we expecting collision with it")
                                    break
                    else:
                        key_match = None
                        collision = None

                    if st.index > 0 and st.index <= u.PIPELINE_CONFIG.WAIT_FOR_WRITE_ACK:
                        op = int(getattr(m, st.transaction_state.operation._sig.name).read())

                        orig_d = st.transaction_state.original_data
                        t_item_valid = int_or_none(getattr(m, orig_d.item_valid._sig.name).read())
                        t_key = int_or_none(getattr(m, orig_d.key._sig.name).read())
                        t_data = data = int_or_none(getattr(m, orig_d.value._sig.name).read())
                    else:
                        op = None
                        t_item_valid = None
                        t_key = None
                        t_data = None
                    
                    item_vld = int_or_none(getattr(m, st.data.item_valid._sig.name).read())
                    if item_vld:
                        key = int_or_none(getattr(m, st.data.key._sig.name).read())
                        data = int_or_none(getattr(m, st.data.value._sig.name).read())
                    else:
                        key = None
                        data = None

                    data = (op, addr, (t_item_valid, t_key, t_data), (item_vld, key, data), collision, key_match)
                else:
                    data = None
                cur_state.append(data)
                    
            if not states or states[-1][1] != cur_state:
                clk_i = tc.hdl_simulator.now // CLK_PERIOD
                states.append((clk_i, cur_state))  
                # print(f"clk {clk_i}: {cur_state}")


def OutOfOrderCummulativeOp_dump_pipeline_html(file: StringIO, u: OooOpExampleCounterHashTable, states: list):
    rows = []
    st_names = {getattr(u.PIPELINE_CONFIG, n): n for n in [
                    "READ_DATA_RECEIVE",
                    "STATE_LOAD",
                    "WRITE_BACK",
                    "WAIT_FOR_WRITE_ACK"]}
    operation_names = {
        getattr(u.OPERATION, n): n for n in [
            "SWAP",
            "LOOKUP_OR_SWAP",
            "LOOKUP",
        ]
    }

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
                (op, addr, (t_item_valid, t_key, t_data), (item_vld, key, data), collision, key_match) = st
                if st_i == 0 or st_i > u.PIPELINE_CONFIG.WAIT_FOR_WRITE_ACK:
                    op = ""  # operation is not present in these stages
                    t = None
                else:
                    op = operation_names.get(op, "INVALID")
                    if t_item_valid is None:
                        t = ""
                    else:
                        t = repr((t_item_valid, t_key, t_data))
 
                if item_vld:
                    d = repr((item_vld, key, data))
                else:
                    d = ""
                
                cell_lines = [f"0x{addr:x} {op:s}<br/>"]
                if t is not None:
                    cell_lines.append(f"t:{t}<br/>")
                cell_lines.append(f"d:{d}<br/>")
                if collision is not None:
                    cell_lines.append(f"collision:{collision}<br/>")
                if key_match is not None:
                    cell_lines.append(f"t_key_match:{key_match}<br/>")

                cell_lines = "".join(cell_lines)
                cell = f"<td>{cell_lines:s}</td>" 
                    
            state_cells.append(cell)   
        
        state_cells = "".join(state_cells)
        row = f"<tr><td>{clk_i}</td>{state_cells:s}</tr>"
        rows.append(row)

    rows = "\n".join(rows)
    file.write(f"<!DOCTYPE html><html><head><meta charset='utf-8'/></head><body><table border='1'>\n{rows}\n</table></body></html>\n")
