from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.param import Param
from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.interfaces.utils import addClkRstn
from hdl_toolkit.interfaces.std import Signal



class Alu(Unit):
    def _config(self):
        self.IMPLEMENT_BCD_INSTRUCTIONS = Param(False)
        # When true, instructions DA and XCHD will work as in the original MCS51.
        # When false, those instructions will work as NOP, saving some logic.
        self.DATA_WIDHT = Param(8)
        
    def _declr(self):
        word_t = vecT(self.DATA_WIDHT)
        with self._asExtern():
            addClkRstn(self)
            self.result = Signal(dtype=word_t)
            self.nobit_result = Signal(dtype=word_t)
            
            self.xdata_wr        = Signal(dtype=word_t)
            self.xdata_rd        = Signal(dtype=word_t)
            
            self.iram_sfr_rd     = Signal(dtype=word_t)
            self.code_rd         = Signal(dtype=word_t)
            self.ACC             = Signal(dtype=word_t)
            self.B               = Signal(dtype=word_t)
            
            self.cy_in           : in std_logic;
            self.ac_in           : in std_logic;
            
            self.result_is_zero  : out std_logic;
            self.acc_is_zero     : out std_logic;
            self.cy_out          : out std_logic;
            self.ov_out          : out std_logic;
            self.p_out           : out std_logic;
            self.op_sel          : in t_alu_op_sel;
            
            
            self.alu_fn_reg      : in t_alu_fns;
            self.bit_index_reg   : in unsigned(2 downto 0);
            self.load_acc_sfr    : in std_logic;
            self.load_acc_out    : out std_logic;
            self.bit_input_out   : out std_logic;
            self.ac_out          : out std_logic;
            
            self.load_b_sfr      : in std_logic;
            self.mul_ready       : out std_logic;
            self.div_ready       : out std_logic;
            
            self.use_bitfield    : in std_logic;
            
            self.ps              : t_cpu_state
        