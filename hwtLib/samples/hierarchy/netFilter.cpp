#include <systemc.h>


SC_MODULE(hfe) {
    //interfaces
    sc_in<sc_uint<64>> din_data;
    sc_in<sc_uint<1>> din_last;
    sc_out<sc_uint<1>> din_ready;
    sc_in<sc_uint<8>> din_strb;
    sc_in<sc_uint<1>> din_valid;
    sc_out<sc_uint<64>> dout_data;
    sc_out<sc_uint<1>> dout_last;
    sc_in<sc_uint<1>> dout_ready;
    sc_out<sc_uint<8>> dout_strb;
    sc_out<sc_uint<1>> dout_valid;
    sc_out<sc_uint<64>> headers_data;
    sc_out<sc_uint<1>> headers_last;
    sc_in<sc_uint<1>> headers_ready;
    sc_out<sc_uint<8>> headers_strb;
    sc_out<sc_uint<1>> headers_valid;

    //processes inside this component
    void assig_process_din_ready() {
        din_ready.write('X');
    }
    void assig_process_dout_data() {
        dout_data.write(sc_uint<64>("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"));
    }
    void assig_process_dout_last() {
        dout_last.write('X');
    }
    void assig_process_dout_strb() {
        dout_strb.write(sc_uint<8>("XXXXXXXX"));
    }
    void assig_process_dout_valid() {
        dout_valid.write('X');
    }
    void assig_process_headers_data() {
        headers_data.write(sc_uint<64>("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"));
    }
    void assig_process_headers_last() {
        headers_last.write('X');
    }
    void assig_process_headers_strb() {
        headers_strb.write(sc_uint<8>("XXXXXXXX"));
    }
    void assig_process_headers_valid() {
        headers_valid.write('X');
    }

    SC_CTOR(hfe) {
        SC_METHOD(assig_process_din_ready);
        
        SC_METHOD(assig_process_dout_data);
        
        SC_METHOD(assig_process_dout_last);
        
        SC_METHOD(assig_process_dout_strb);
        
        SC_METHOD(assig_process_dout_valid);
        
        SC_METHOD(assig_process_headers_data);
        
        SC_METHOD(assig_process_headers_last);
        
        SC_METHOD(assig_process_headers_strb);
        
        SC_METHOD(assig_process_headers_valid);
        
    }
};
#include <systemc.h>


SC_MODULE(patternMatch) {
    //interfaces
    sc_in<sc_uint<64>> din_data;
    sc_in<sc_uint<1>> din_last;
    sc_out<sc_uint<1>> din_ready;
    sc_in<sc_uint<8>> din_strb;
    sc_in<sc_uint<1>> din_valid;
    sc_out<sc_uint<64>> match_data;
    sc_out<sc_uint<1>> match_last;
    sc_in<sc_uint<1>> match_ready;
    sc_out<sc_uint<8>> match_strb;
    sc_out<sc_uint<1>> match_valid;

    //processes inside this component
    void assig_process_din_ready() {
        din_ready.write('X');
    }
    void assig_process_match_data() {
        match_data.write(sc_uint<64>("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"));
    }
    void assig_process_match_last() {
        match_last.write('X');
    }
    void assig_process_match_strb() {
        match_strb.write(sc_uint<8>("XXXXXXXX"));
    }
    void assig_process_match_valid() {
        match_valid.write('X');
    }

    SC_CTOR(patternMatch) {
        SC_METHOD(assig_process_din_ready);
        
        SC_METHOD(assig_process_match_data);
        
        SC_METHOD(assig_process_match_last);
        
        SC_METHOD(assig_process_match_strb);
        
        SC_METHOD(assig_process_match_valid);
        
    }
};
#include <systemc.h>


SC_MODULE(filter) {
    //interfaces
    sc_in<sc_uint<32>> cfg_ar_addr;
    sc_in<sc_uint<3>> cfg_ar_prot;
    sc_out<sc_uint<1>> cfg_ar_ready;
    sc_in<sc_uint<1>> cfg_ar_valid;
    sc_in<sc_uint<32>> cfg_aw_addr;
    sc_in<sc_uint<3>> cfg_aw_prot;
    sc_out<sc_uint<1>> cfg_aw_ready;
    sc_in<sc_uint<1>> cfg_aw_valid;
    sc_in<sc_uint<1>> cfg_b_ready;
    sc_out<sc_uint<2>> cfg_b_resp;
    sc_out<sc_uint<1>> cfg_b_valid;
    sc_out<sc_uint<64>> cfg_r_data;
    sc_in<sc_uint<1>> cfg_r_ready;
    sc_out<sc_uint<2>> cfg_r_resp;
    sc_out<sc_uint<1>> cfg_r_valid;
    sc_in<sc_uint<64>> cfg_w_data;
    sc_out<sc_uint<1>> cfg_w_ready;
    sc_in<sc_uint<8>> cfg_w_strb;
    sc_in<sc_uint<1>> cfg_w_valid;
    sc_in<sc_uint<64>> din_data;
    sc_in<sc_uint<1>> din_last;
    sc_out<sc_uint<1>> din_ready;
    sc_in<sc_uint<8>> din_strb;
    sc_in<sc_uint<1>> din_valid;
    sc_out<sc_uint<64>> dout_data;
    sc_out<sc_uint<1>> dout_last;
    sc_in<sc_uint<1>> dout_ready;
    sc_out<sc_uint<8>> dout_strb;
    sc_out<sc_uint<1>> dout_valid;
    sc_in<sc_uint<64>> headers_data;
    sc_in<sc_uint<1>> headers_last;
    sc_out<sc_uint<1>> headers_ready;
    sc_in<sc_uint<8>> headers_strb;
    sc_in<sc_uint<1>> headers_valid;
    sc_in<sc_uint<64>> patternMatch_data;
    sc_in<sc_uint<1>> patternMatch_last;
    sc_out<sc_uint<1>> patternMatch_ready;
    sc_in<sc_uint<8>> patternMatch_strb;
    sc_in<sc_uint<1>> patternMatch_valid;

    //processes inside this component
    void assig_process_cfg_ar_ready() {
        cfg_ar_ready.write('X');
    }
    void assig_process_cfg_aw_ready() {
        cfg_aw_ready.write('X');
    }
    void assig_process_cfg_b_resp() {
        cfg_b_resp.write(sc_uint<2>("XX"));
    }
    void assig_process_cfg_b_valid() {
        cfg_b_valid.write('X');
    }
    void assig_process_cfg_r_data() {
        cfg_r_data.write(sc_uint<64>("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"));
    }
    void assig_process_cfg_r_resp() {
        cfg_r_resp.write(sc_uint<2>("XX"));
    }
    void assig_process_cfg_r_valid() {
        cfg_r_valid.write('X');
    }
    void assig_process_cfg_w_ready() {
        cfg_w_ready.write('X');
    }
    void assig_process_din_ready() {
        din_ready.write('X');
    }
    void assig_process_dout_data() {
        dout_data.write(sc_uint<64>("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"));
    }
    void assig_process_dout_last() {
        dout_last.write('X');
    }
    void assig_process_dout_strb() {
        dout_strb.write(sc_uint<8>("XXXXXXXX"));
    }
    void assig_process_dout_valid() {
        dout_valid.write('X');
    }
    void assig_process_headers_ready() {
        headers_ready.write('X');
    }
    void assig_process_patternMatch_ready() {
        patternMatch_ready.write('X');
    }

    SC_CTOR(filter) {
        SC_METHOD(assig_process_cfg_ar_ready);
        
        SC_METHOD(assig_process_cfg_aw_ready);
        
        SC_METHOD(assig_process_cfg_b_resp);
        
        SC_METHOD(assig_process_cfg_b_valid);
        
        SC_METHOD(assig_process_cfg_r_data);
        
        SC_METHOD(assig_process_cfg_r_resp);
        
        SC_METHOD(assig_process_cfg_r_valid);
        
        SC_METHOD(assig_process_cfg_w_ready);
        
        SC_METHOD(assig_process_din_ready);
        
        SC_METHOD(assig_process_dout_data);
        
        SC_METHOD(assig_process_dout_last);
        
        SC_METHOD(assig_process_dout_strb);
        
        SC_METHOD(assig_process_dout_valid);
        
        SC_METHOD(assig_process_headers_ready);
        
        SC_METHOD(assig_process_patternMatch_ready);
        
    }
};
#include <systemc.h>


SC_MODULE(exporter) {
    //interfaces
    sc_in<sc_uint<64>> din_data;
    sc_in<sc_uint<1>> din_last;
    sc_out<sc_uint<1>> din_ready;
    sc_in<sc_uint<8>> din_strb;
    sc_in<sc_uint<1>> din_valid;
    sc_out<sc_uint<64>> dout_data;
    sc_out<sc_uint<1>> dout_last;
    sc_in<sc_uint<1>> dout_ready;
    sc_out<sc_uint<8>> dout_strb;
    sc_out<sc_uint<1>> dout_valid;

    //processes inside this component
    void assig_process_din_ready() {
        din_ready.write('X');
    }
    void assig_process_dout_data() {
        dout_data.write(sc_uint<64>("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"));
    }
    void assig_process_dout_last() {
        dout_last.write('X');
    }
    void assig_process_dout_strb() {
        dout_strb.write(sc_uint<8>("XXXXXXXX"));
    }
    void assig_process_dout_valid() {
        dout_valid.write('X');
    }

    SC_CTOR(exporter) {
        SC_METHOD(assig_process_din_ready);
        
        SC_METHOD(assig_process_dout_data);
        
        SC_METHOD(assig_process_dout_last);
        
        SC_METHOD(assig_process_dout_strb);
        
        SC_METHOD(assig_process_dout_valid);
        
    }
};
#include <systemc.h>


SC_MODULE(gen_dout_splitCopy_0) {
    //interfaces
    sc_in<sc_uint<64>> dataIn_data;
    sc_in<sc_uint<1>> dataIn_last;
    sc_out<sc_uint<1>> dataIn_ready;
    sc_in<sc_uint<8>> dataIn_strb;
    sc_in<sc_uint<1>> dataIn_valid;
    sc_out<sc_uint<64>> dataOut_0_data;
    sc_out<sc_uint<1>> dataOut_0_last;
    sc_in<sc_uint<1>> dataOut_0_ready;
    sc_out<sc_uint<8>> dataOut_0_strb;
    sc_out<sc_uint<1>> dataOut_0_valid;
    sc_out<sc_uint<64>> dataOut_1_data;
    sc_out<sc_uint<1>> dataOut_1_last;
    sc_in<sc_uint<1>> dataOut_1_ready;
    sc_out<sc_uint<8>> dataOut_1_strb;
    sc_out<sc_uint<1>> dataOut_1_valid;

    //processes inside this component
    void assig_process_dataIn_ready() {
        dataIn_ready.write(dataOut_0_ready.read() & dataOut_1_ready.read());
    }
    void assig_process_dataOut_0_data() {
        dataOut_0_data.write(dataIn_data.read());
    }
    void assig_process_dataOut_0_last() {
        dataOut_0_last.write(dataIn_last.read());
    }
    void assig_process_dataOut_0_strb() {
        dataOut_0_strb.write(dataIn_strb.read());
    }
    void assig_process_dataOut_0_valid() {
        dataOut_0_valid.write(dataIn_valid.read() & dataOut_1_ready.read());
    }
    void assig_process_dataOut_1_data() {
        dataOut_1_data.write(dataIn_data.read());
    }
    void assig_process_dataOut_1_last() {
        dataOut_1_last.write(dataIn_last.read());
    }
    void assig_process_dataOut_1_strb() {
        dataOut_1_strb.write(dataIn_strb.read());
    }
    void assig_process_dataOut_1_valid() {
        dataOut_1_valid.write(dataIn_valid.read() & dataOut_0_ready.read());
    }

    SC_CTOR(gen_dout_splitCopy_0) {
        SC_METHOD(assig_process_dataIn_ready);
        sensitive << dataOut_0_ready << dataOut_1_ready;
        SC_METHOD(assig_process_dataOut_0_data);
        sensitive << dataIn_data;
        SC_METHOD(assig_process_dataOut_0_last);
        sensitive << dataIn_last;
        SC_METHOD(assig_process_dataOut_0_strb);
        sensitive << dataIn_strb;
        SC_METHOD(assig_process_dataOut_0_valid);
        sensitive << dataIn_valid << dataOut_1_ready;
        SC_METHOD(assig_process_dataOut_1_data);
        sensitive << dataIn_data;
        SC_METHOD(assig_process_dataOut_1_last);
        sensitive << dataIn_last;
        SC_METHOD(assig_process_dataOut_1_strb);
        sensitive << dataIn_strb;
        SC_METHOD(assig_process_dataOut_1_valid);
        sensitive << dataIn_valid << dataOut_0_ready;
    }
};
/*

    This unit has actually no functionality it is just example
    of hierarchical design.
    
*/

#include <systemc.h>


SC_MODULE(NetFilter) {
    //interfaces
    sc_in<sc_uint<32>> cfg_ar_addr;
    sc_in<sc_uint<3>> cfg_ar_prot;
    sc_out<sc_uint<1>> cfg_ar_ready;
    sc_in<sc_uint<1>> cfg_ar_valid;
    sc_in<sc_uint<32>> cfg_aw_addr;
    sc_in<sc_uint<3>> cfg_aw_prot;
    sc_out<sc_uint<1>> cfg_aw_ready;
    sc_in<sc_uint<1>> cfg_aw_valid;
    sc_in<sc_uint<1>> cfg_b_ready;
    sc_out<sc_uint<2>> cfg_b_resp;
    sc_out<sc_uint<1>> cfg_b_valid;
    sc_out<sc_uint<64>> cfg_r_data;
    sc_in<sc_uint<1>> cfg_r_ready;
    sc_out<sc_uint<2>> cfg_r_resp;
    sc_out<sc_uint<1>> cfg_r_valid;
    sc_in<sc_uint<64>> cfg_w_data;
    sc_out<sc_uint<1>> cfg_w_ready;
    sc_in<sc_uint<8>> cfg_w_strb;
    sc_in<sc_uint<1>> cfg_w_valid;
    sc_in_clk clk;
    sc_in<sc_uint<64>> din_data;
    sc_in<sc_uint<1>> din_last;
    sc_out<sc_uint<1>> din_ready;
    sc_in<sc_uint<8>> din_strb;
    sc_in<sc_uint<1>> din_valid;
    sc_out<sc_uint<64>> export_data;
    sc_out<sc_uint<1>> export_last;
    sc_in<sc_uint<1>> export_ready;
    sc_out<sc_uint<8>> export_strb;
    sc_out<sc_uint<1>> export_valid;
    sc_in<sc_uint<1>> rst_n;

    //internal signals
    sc_signal<sc_uint<64>> sig_exporter_din_data;
    sc_signal<sc_uint<1>> sig_exporter_din_last;
    sc_signal<sc_uint<1>> sig_exporter_din_ready;
    sc_signal<sc_uint<8>> sig_exporter_din_strb;
    sc_signal<sc_uint<1>> sig_exporter_din_valid;
    sc_signal<sc_uint<64>> sig_exporter_dout_data;
    sc_signal<sc_uint<1>> sig_exporter_dout_last;
    sc_signal<sc_uint<1>> sig_exporter_dout_ready;
    sc_signal<sc_uint<8>> sig_exporter_dout_strb;
    sc_signal<sc_uint<1>> sig_exporter_dout_valid;
    sc_signal<sc_uint<32>> sig_filter_cfg_ar_addr;
    sc_signal<sc_uint<3>> sig_filter_cfg_ar_prot;
    sc_signal<sc_uint<1>> sig_filter_cfg_ar_ready;
    sc_signal<sc_uint<1>> sig_filter_cfg_ar_valid;
    sc_signal<sc_uint<32>> sig_filter_cfg_aw_addr;
    sc_signal<sc_uint<3>> sig_filter_cfg_aw_prot;
    sc_signal<sc_uint<1>> sig_filter_cfg_aw_ready;
    sc_signal<sc_uint<1>> sig_filter_cfg_aw_valid;
    sc_signal<sc_uint<1>> sig_filter_cfg_b_ready;
    sc_signal<sc_uint<2>> sig_filter_cfg_b_resp;
    sc_signal<sc_uint<1>> sig_filter_cfg_b_valid;
    sc_signal<sc_uint<64>> sig_filter_cfg_r_data;
    sc_signal<sc_uint<1>> sig_filter_cfg_r_ready;
    sc_signal<sc_uint<2>> sig_filter_cfg_r_resp;
    sc_signal<sc_uint<1>> sig_filter_cfg_r_valid;
    sc_signal<sc_uint<64>> sig_filter_cfg_w_data;
    sc_signal<sc_uint<1>> sig_filter_cfg_w_ready;
    sc_signal<sc_uint<8>> sig_filter_cfg_w_strb;
    sc_signal<sc_uint<1>> sig_filter_cfg_w_valid;
    sc_signal<sc_uint<64>> sig_filter_din_data;
    sc_signal<sc_uint<1>> sig_filter_din_last;
    sc_signal<sc_uint<1>> sig_filter_din_ready;
    sc_signal<sc_uint<8>> sig_filter_din_strb;
    sc_signal<sc_uint<1>> sig_filter_din_valid;
    sc_signal<sc_uint<64>> sig_filter_dout_data;
    sc_signal<sc_uint<1>> sig_filter_dout_last;
    sc_signal<sc_uint<1>> sig_filter_dout_ready;
    sc_signal<sc_uint<8>> sig_filter_dout_strb;
    sc_signal<sc_uint<1>> sig_filter_dout_valid;
    sc_signal<sc_uint<64>> sig_filter_headers_data;
    sc_signal<sc_uint<1>> sig_filter_headers_last;
    sc_signal<sc_uint<1>> sig_filter_headers_ready;
    sc_signal<sc_uint<8>> sig_filter_headers_strb;
    sc_signal<sc_uint<1>> sig_filter_headers_valid;
    sc_signal<sc_uint<64>> sig_filter_patternMatch_data;
    sc_signal<sc_uint<1>> sig_filter_patternMatch_last;
    sc_signal<sc_uint<1>> sig_filter_patternMatch_ready;
    sc_signal<sc_uint<8>> sig_filter_patternMatch_strb;
    sc_signal<sc_uint<1>> sig_filter_patternMatch_valid;
    sc_signal<sc_uint<64>> sig_gen_dout_splitCopy_0_dataIn_data;
    sc_signal<sc_uint<1>> sig_gen_dout_splitCopy_0_dataIn_last;
    sc_signal<sc_uint<1>> sig_gen_dout_splitCopy_0_dataIn_ready;
    sc_signal<sc_uint<8>> sig_gen_dout_splitCopy_0_dataIn_strb;
    sc_signal<sc_uint<1>> sig_gen_dout_splitCopy_0_dataIn_valid;
    sc_signal<sc_uint<64>> sig_gen_dout_splitCopy_0_dataOut_0_data;
    sc_signal<sc_uint<1>> sig_gen_dout_splitCopy_0_dataOut_0_last;
    sc_signal<sc_uint<1>> sig_gen_dout_splitCopy_0_dataOut_0_ready;
    sc_signal<sc_uint<8>> sig_gen_dout_splitCopy_0_dataOut_0_strb;
    sc_signal<sc_uint<1>> sig_gen_dout_splitCopy_0_dataOut_0_valid;
    sc_signal<sc_uint<64>> sig_gen_dout_splitCopy_0_dataOut_1_data;
    sc_signal<sc_uint<1>> sig_gen_dout_splitCopy_0_dataOut_1_last;
    sc_signal<sc_uint<1>> sig_gen_dout_splitCopy_0_dataOut_1_ready;
    sc_signal<sc_uint<8>> sig_gen_dout_splitCopy_0_dataOut_1_strb;
    sc_signal<sc_uint<1>> sig_gen_dout_splitCopy_0_dataOut_1_valid;
    sc_signal<sc_uint<64>> sig_hfe_din_data;
    sc_signal<sc_uint<1>> sig_hfe_din_last;
    sc_signal<sc_uint<1>> sig_hfe_din_ready;
    sc_signal<sc_uint<8>> sig_hfe_din_strb;
    sc_signal<sc_uint<1>> sig_hfe_din_valid;
    sc_signal<sc_uint<64>> sig_hfe_dout_data;
    sc_signal<sc_uint<1>> sig_hfe_dout_last;
    sc_signal<sc_uint<1>> sig_hfe_dout_ready;
    sc_signal<sc_uint<8>> sig_hfe_dout_strb;
    sc_signal<sc_uint<1>> sig_hfe_dout_valid;
    sc_signal<sc_uint<64>> sig_hfe_headers_data;
    sc_signal<sc_uint<1>> sig_hfe_headers_last;
    sc_signal<sc_uint<1>> sig_hfe_headers_ready;
    sc_signal<sc_uint<8>> sig_hfe_headers_strb;
    sc_signal<sc_uint<1>> sig_hfe_headers_valid;
    sc_signal<sc_uint<64>> sig_patternMatch_din_data;
    sc_signal<sc_uint<1>> sig_patternMatch_din_last;
    sc_signal<sc_uint<1>> sig_patternMatch_din_ready;
    sc_signal<sc_uint<8>> sig_patternMatch_din_strb;
    sc_signal<sc_uint<1>> sig_patternMatch_din_valid;
    sc_signal<sc_uint<64>> sig_patternMatch_match_data;
    sc_signal<sc_uint<1>> sig_patternMatch_match_last;
    sc_signal<sc_uint<1>> sig_patternMatch_match_ready;
    sc_signal<sc_uint<8>> sig_patternMatch_match_strb;
    sc_signal<sc_uint<1>> sig_patternMatch_match_valid;

    //processes inside this component
    void assig_process_cfg_ar_ready() {
        cfg_ar_ready.write(sig_filter_cfg_ar_ready.read());
    }
    void assig_process_cfg_aw_ready() {
        cfg_aw_ready.write(sig_filter_cfg_aw_ready.read());
    }
    void assig_process_cfg_b_resp() {
        cfg_b_resp.write(sig_filter_cfg_b_resp.read());
    }
    void assig_process_cfg_b_valid() {
        cfg_b_valid.write(sig_filter_cfg_b_valid.read());
    }
    void assig_process_cfg_r_data() {
        cfg_r_data.write(sig_filter_cfg_r_data.read());
    }
    void assig_process_cfg_r_resp() {
        cfg_r_resp.write(sig_filter_cfg_r_resp.read());
    }
    void assig_process_cfg_r_valid() {
        cfg_r_valid.write(sig_filter_cfg_r_valid.read());
    }
    void assig_process_cfg_w_ready() {
        cfg_w_ready.write(sig_filter_cfg_w_ready.read());
    }
    void assig_process_din_ready() {
        din_ready.write(sig_hfe_din_ready.read());
    }
    void assig_process_export_data() {
        export_data.write(sig_exporter_dout_data.read());
    }
    void assig_process_export_last() {
        export_last.write(sig_exporter_dout_last.read());
    }
    void assig_process_export_strb() {
        export_strb.write(sig_exporter_dout_strb.read());
    }
    void assig_process_export_valid() {
        export_valid.write(sig_exporter_dout_valid.read());
    }
    void assig_process_sig_exporter_din_data() {
        sig_exporter_din_data.write(sig_filter_dout_data.read());
    }
    void assig_process_sig_exporter_din_last() {
        sig_exporter_din_last.write(sig_filter_dout_last.read());
    }
    void assig_process_sig_exporter_din_strb() {
        sig_exporter_din_strb.write(sig_filter_dout_strb.read());
    }
    void assig_process_sig_exporter_din_valid() {
        sig_exporter_din_valid.write(sig_filter_dout_valid.read());
    }
    void assig_process_sig_exporter_dout_ready() {
        sig_exporter_dout_ready.write(export_ready.read());
    }
    void assig_process_sig_filter_cfg_ar_addr() {
        sig_filter_cfg_ar_addr.write(cfg_ar_addr.read());
    }
    void assig_process_sig_filter_cfg_ar_prot() {
        sig_filter_cfg_ar_prot.write(cfg_ar_prot.read());
    }
    void assig_process_sig_filter_cfg_ar_valid() {
        sig_filter_cfg_ar_valid.write(cfg_ar_valid.read());
    }
    void assig_process_sig_filter_cfg_aw_addr() {
        sig_filter_cfg_aw_addr.write(cfg_aw_addr.read());
    }
    void assig_process_sig_filter_cfg_aw_prot() {
        sig_filter_cfg_aw_prot.write(cfg_aw_prot.read());
    }
    void assig_process_sig_filter_cfg_aw_valid() {
        sig_filter_cfg_aw_valid.write(cfg_aw_valid.read());
    }
    void assig_process_sig_filter_cfg_b_ready() {
        sig_filter_cfg_b_ready.write(cfg_b_ready.read());
    }
    void assig_process_sig_filter_cfg_r_ready() {
        sig_filter_cfg_r_ready.write(cfg_r_ready.read());
    }
    void assig_process_sig_filter_cfg_w_data() {
        sig_filter_cfg_w_data.write(cfg_w_data.read());
    }
    void assig_process_sig_filter_cfg_w_strb() {
        sig_filter_cfg_w_strb.write(cfg_w_strb.read());
    }
    void assig_process_sig_filter_cfg_w_valid() {
        sig_filter_cfg_w_valid.write(cfg_w_valid.read());
    }
    void assig_process_sig_filter_din_data() {
        sig_filter_din_data.write(sig_gen_dout_splitCopy_0_dataOut_1_data.read());
    }
    void assig_process_sig_filter_din_last() {
        sig_filter_din_last.write(sig_gen_dout_splitCopy_0_dataOut_1_last.read());
    }
    void assig_process_sig_filter_din_strb() {
        sig_filter_din_strb.write(sig_gen_dout_splitCopy_0_dataOut_1_strb.read());
    }
    void assig_process_sig_filter_din_valid() {
        sig_filter_din_valid.write(sig_gen_dout_splitCopy_0_dataOut_1_valid.read());
    }
    void assig_process_sig_filter_dout_ready() {
        sig_filter_dout_ready.write(sig_exporter_din_ready.read());
    }
    void assig_process_sig_filter_headers_data() {
        sig_filter_headers_data.write(sig_hfe_headers_data.read());
    }
    void assig_process_sig_filter_headers_last() {
        sig_filter_headers_last.write(sig_hfe_headers_last.read());
    }
    void assig_process_sig_filter_headers_strb() {
        sig_filter_headers_strb.write(sig_hfe_headers_strb.read());
    }
    void assig_process_sig_filter_headers_valid() {
        sig_filter_headers_valid.write(sig_hfe_headers_valid.read());
    }
    void assig_process_sig_filter_patternMatch_data() {
        sig_filter_patternMatch_data.write(sig_patternMatch_match_data.read());
    }
    void assig_process_sig_filter_patternMatch_last() {
        sig_filter_patternMatch_last.write(sig_patternMatch_match_last.read());
    }
    void assig_process_sig_filter_patternMatch_strb() {
        sig_filter_patternMatch_strb.write(sig_patternMatch_match_strb.read());
    }
    void assig_process_sig_filter_patternMatch_valid() {
        sig_filter_patternMatch_valid.write(sig_patternMatch_match_valid.read());
    }
    void assig_process_sig_gen_dout_splitCopy_0_dataIn_data() {
        sig_gen_dout_splitCopy_0_dataIn_data.write(sig_hfe_dout_data.read());
    }
    void assig_process_sig_gen_dout_splitCopy_0_dataIn_last() {
        sig_gen_dout_splitCopy_0_dataIn_last.write(sig_hfe_dout_last.read());
    }
    void assig_process_sig_gen_dout_splitCopy_0_dataIn_strb() {
        sig_gen_dout_splitCopy_0_dataIn_strb.write(sig_hfe_dout_strb.read());
    }
    void assig_process_sig_gen_dout_splitCopy_0_dataIn_valid() {
        sig_gen_dout_splitCopy_0_dataIn_valid.write(sig_hfe_dout_valid.read());
    }
    void assig_process_sig_gen_dout_splitCopy_0_dataOut_0_ready() {
        sig_gen_dout_splitCopy_0_dataOut_0_ready.write(sig_patternMatch_din_ready.read());
    }
    void assig_process_sig_gen_dout_splitCopy_0_dataOut_1_ready() {
        sig_gen_dout_splitCopy_0_dataOut_1_ready.write(sig_filter_din_ready.read());
    }
    void assig_process_sig_hfe_din_data() {
        sig_hfe_din_data.write(din_data.read());
    }
    void assig_process_sig_hfe_din_last() {
        sig_hfe_din_last.write(din_last.read());
    }
    void assig_process_sig_hfe_din_strb() {
        sig_hfe_din_strb.write(din_strb.read());
    }
    void assig_process_sig_hfe_din_valid() {
        sig_hfe_din_valid.write(din_valid.read());
    }
    void assig_process_sig_hfe_dout_ready() {
        sig_hfe_dout_ready.write(sig_gen_dout_splitCopy_0_dataIn_ready.read());
    }
    void assig_process_sig_hfe_headers_ready() {
        sig_hfe_headers_ready.write(sig_filter_headers_ready.read());
    }
    void assig_process_sig_patternMatch_din_data() {
        sig_patternMatch_din_data.write(sig_gen_dout_splitCopy_0_dataOut_0_data.read());
    }
    void assig_process_sig_patternMatch_din_last() {
        sig_patternMatch_din_last.write(sig_gen_dout_splitCopy_0_dataOut_0_last.read());
    }
    void assig_process_sig_patternMatch_din_strb() {
        sig_patternMatch_din_strb.write(sig_gen_dout_splitCopy_0_dataOut_0_strb.read());
    }
    void assig_process_sig_patternMatch_din_valid() {
        sig_patternMatch_din_valid.write(sig_gen_dout_splitCopy_0_dataOut_0_valid.read());
    }
    void assig_process_sig_patternMatch_match_ready() {
        sig_patternMatch_match_ready.write(sig_filter_patternMatch_ready.read());
    }

    // components inside this component

    exporter exporter_inst;
    filter filter_inst;
    gen_dout_splitCopy_0 gen_dout_splitCopy_0_inst;
    hfe hfe_inst;
    patternMatch patternMatch_inst;

    SC_CTOR(NetFilter) : exporter_inst("exporter_inst"), filter_inst("filter_inst"), gen_dout_splitCopy_0_inst("gen_dout_splitCopy_0_inst"), hfe_inst("hfe_inst"), patternMatch_inst("patternMatch_inst") {
        SC_METHOD(assig_process_cfg_ar_ready);
        sensitive << sig_filter_cfg_ar_ready;
        SC_METHOD(assig_process_cfg_aw_ready);
        sensitive << sig_filter_cfg_aw_ready;
        SC_METHOD(assig_process_cfg_b_resp);
        sensitive << sig_filter_cfg_b_resp;
        SC_METHOD(assig_process_cfg_b_valid);
        sensitive << sig_filter_cfg_b_valid;
        SC_METHOD(assig_process_cfg_r_data);
        sensitive << sig_filter_cfg_r_data;
        SC_METHOD(assig_process_cfg_r_resp);
        sensitive << sig_filter_cfg_r_resp;
        SC_METHOD(assig_process_cfg_r_valid);
        sensitive << sig_filter_cfg_r_valid;
        SC_METHOD(assig_process_cfg_w_ready);
        sensitive << sig_filter_cfg_w_ready;
        SC_METHOD(assig_process_din_ready);
        sensitive << sig_hfe_din_ready;
        SC_METHOD(assig_process_export_data);
        sensitive << sig_exporter_dout_data;
        SC_METHOD(assig_process_export_last);
        sensitive << sig_exporter_dout_last;
        SC_METHOD(assig_process_export_strb);
        sensitive << sig_exporter_dout_strb;
        SC_METHOD(assig_process_export_valid);
        sensitive << sig_exporter_dout_valid;
        SC_METHOD(assig_process_sig_exporter_din_data);
        sensitive << sig_filter_dout_data;
        SC_METHOD(assig_process_sig_exporter_din_last);
        sensitive << sig_filter_dout_last;
        SC_METHOD(assig_process_sig_exporter_din_strb);
        sensitive << sig_filter_dout_strb;
        SC_METHOD(assig_process_sig_exporter_din_valid);
        sensitive << sig_filter_dout_valid;
        SC_METHOD(assig_process_sig_exporter_dout_ready);
        sensitive << export_ready;
        SC_METHOD(assig_process_sig_filter_cfg_ar_addr);
        sensitive << cfg_ar_addr;
        SC_METHOD(assig_process_sig_filter_cfg_ar_prot);
        sensitive << cfg_ar_prot;
        SC_METHOD(assig_process_sig_filter_cfg_ar_valid);
        sensitive << cfg_ar_valid;
        SC_METHOD(assig_process_sig_filter_cfg_aw_addr);
        sensitive << cfg_aw_addr;
        SC_METHOD(assig_process_sig_filter_cfg_aw_prot);
        sensitive << cfg_aw_prot;
        SC_METHOD(assig_process_sig_filter_cfg_aw_valid);
        sensitive << cfg_aw_valid;
        SC_METHOD(assig_process_sig_filter_cfg_b_ready);
        sensitive << cfg_b_ready;
        SC_METHOD(assig_process_sig_filter_cfg_r_ready);
        sensitive << cfg_r_ready;
        SC_METHOD(assig_process_sig_filter_cfg_w_data);
        sensitive << cfg_w_data;
        SC_METHOD(assig_process_sig_filter_cfg_w_strb);
        sensitive << cfg_w_strb;
        SC_METHOD(assig_process_sig_filter_cfg_w_valid);
        sensitive << cfg_w_valid;
        SC_METHOD(assig_process_sig_filter_din_data);
        sensitive << sig_gen_dout_splitCopy_0_dataOut_1_data;
        SC_METHOD(assig_process_sig_filter_din_last);
        sensitive << sig_gen_dout_splitCopy_0_dataOut_1_last;
        SC_METHOD(assig_process_sig_filter_din_strb);
        sensitive << sig_gen_dout_splitCopy_0_dataOut_1_strb;
        SC_METHOD(assig_process_sig_filter_din_valid);
        sensitive << sig_gen_dout_splitCopy_0_dataOut_1_valid;
        SC_METHOD(assig_process_sig_filter_dout_ready);
        sensitive << sig_exporter_din_ready;
        SC_METHOD(assig_process_sig_filter_headers_data);
        sensitive << sig_hfe_headers_data;
        SC_METHOD(assig_process_sig_filter_headers_last);
        sensitive << sig_hfe_headers_last;
        SC_METHOD(assig_process_sig_filter_headers_strb);
        sensitive << sig_hfe_headers_strb;
        SC_METHOD(assig_process_sig_filter_headers_valid);
        sensitive << sig_hfe_headers_valid;
        SC_METHOD(assig_process_sig_filter_patternMatch_data);
        sensitive << sig_patternMatch_match_data;
        SC_METHOD(assig_process_sig_filter_patternMatch_last);
        sensitive << sig_patternMatch_match_last;
        SC_METHOD(assig_process_sig_filter_patternMatch_strb);
        sensitive << sig_patternMatch_match_strb;
        SC_METHOD(assig_process_sig_filter_patternMatch_valid);
        sensitive << sig_patternMatch_match_valid;
        SC_METHOD(assig_process_sig_gen_dout_splitCopy_0_dataIn_data);
        sensitive << sig_hfe_dout_data;
        SC_METHOD(assig_process_sig_gen_dout_splitCopy_0_dataIn_last);
        sensitive << sig_hfe_dout_last;
        SC_METHOD(assig_process_sig_gen_dout_splitCopy_0_dataIn_strb);
        sensitive << sig_hfe_dout_strb;
        SC_METHOD(assig_process_sig_gen_dout_splitCopy_0_dataIn_valid);
        sensitive << sig_hfe_dout_valid;
        SC_METHOD(assig_process_sig_gen_dout_splitCopy_0_dataOut_0_ready);
        sensitive << sig_patternMatch_din_ready;
        SC_METHOD(assig_process_sig_gen_dout_splitCopy_0_dataOut_1_ready);
        sensitive << sig_filter_din_ready;
        SC_METHOD(assig_process_sig_hfe_din_data);
        sensitive << din_data;
        SC_METHOD(assig_process_sig_hfe_din_last);
        sensitive << din_last;
        SC_METHOD(assig_process_sig_hfe_din_strb);
        sensitive << din_strb;
        SC_METHOD(assig_process_sig_hfe_din_valid);
        sensitive << din_valid;
        SC_METHOD(assig_process_sig_hfe_dout_ready);
        sensitive << sig_gen_dout_splitCopy_0_dataIn_ready;
        SC_METHOD(assig_process_sig_hfe_headers_ready);
        sensitive << sig_filter_headers_ready;
        SC_METHOD(assig_process_sig_patternMatch_din_data);
        sensitive << sig_gen_dout_splitCopy_0_dataOut_0_data;
        SC_METHOD(assig_process_sig_patternMatch_din_last);
        sensitive << sig_gen_dout_splitCopy_0_dataOut_0_last;
        SC_METHOD(assig_process_sig_patternMatch_din_strb);
        sensitive << sig_gen_dout_splitCopy_0_dataOut_0_strb;
        SC_METHOD(assig_process_sig_patternMatch_din_valid);
        sensitive << sig_gen_dout_splitCopy_0_dataOut_0_valid;
        SC_METHOD(assig_process_sig_patternMatch_match_ready);
        sensitive << sig_filter_patternMatch_ready;

        // connect ports
        exporter.din_data(sig_exporter_din_data);
        exporter.din_last(sig_exporter_din_last);
        exporter.din_ready(sig_exporter_din_ready);
        exporter.din_strb(sig_exporter_din_strb);
        exporter.din_valid(sig_exporter_din_valid);
        exporter.dout_data(sig_exporter_dout_data);
        exporter.dout_last(sig_exporter_dout_last);
        exporter.dout_ready(sig_exporter_dout_ready);
        exporter.dout_strb(sig_exporter_dout_strb);
        exporter.dout_valid(sig_exporter_dout_valid);
        filter.cfg_ar_addr(sig_filter_cfg_ar_addr);
        filter.cfg_ar_prot(sig_filter_cfg_ar_prot);
        filter.cfg_ar_ready(sig_filter_cfg_ar_ready);
        filter.cfg_ar_valid(sig_filter_cfg_ar_valid);
        filter.cfg_aw_addr(sig_filter_cfg_aw_addr);
        filter.cfg_aw_prot(sig_filter_cfg_aw_prot);
        filter.cfg_aw_ready(sig_filter_cfg_aw_ready);
        filter.cfg_aw_valid(sig_filter_cfg_aw_valid);
        filter.cfg_b_ready(sig_filter_cfg_b_ready);
        filter.cfg_b_resp(sig_filter_cfg_b_resp);
        filter.cfg_b_valid(sig_filter_cfg_b_valid);
        filter.cfg_r_data(sig_filter_cfg_r_data);
        filter.cfg_r_ready(sig_filter_cfg_r_ready);
        filter.cfg_r_resp(sig_filter_cfg_r_resp);
        filter.cfg_r_valid(sig_filter_cfg_r_valid);
        filter.cfg_w_data(sig_filter_cfg_w_data);
        filter.cfg_w_ready(sig_filter_cfg_w_ready);
        filter.cfg_w_strb(sig_filter_cfg_w_strb);
        filter.cfg_w_valid(sig_filter_cfg_w_valid);
        filter.din_data(sig_filter_din_data);
        filter.din_last(sig_filter_din_last);
        filter.din_ready(sig_filter_din_ready);
        filter.din_strb(sig_filter_din_strb);
        filter.din_valid(sig_filter_din_valid);
        filter.dout_data(sig_filter_dout_data);
        filter.dout_last(sig_filter_dout_last);
        filter.dout_ready(sig_filter_dout_ready);
        filter.dout_strb(sig_filter_dout_strb);
        filter.dout_valid(sig_filter_dout_valid);
        filter.headers_data(sig_filter_headers_data);
        filter.headers_last(sig_filter_headers_last);
        filter.headers_ready(sig_filter_headers_ready);
        filter.headers_strb(sig_filter_headers_strb);
        filter.headers_valid(sig_filter_headers_valid);
        filter.patternMatch_data(sig_filter_patternMatch_data);
        filter.patternMatch_last(sig_filter_patternMatch_last);
        filter.patternMatch_ready(sig_filter_patternMatch_ready);
        filter.patternMatch_strb(sig_filter_patternMatch_strb);
        filter.patternMatch_valid(sig_filter_patternMatch_valid);
        gen_dout_splitCopy_0.dataIn_data(sig_gen_dout_splitCopy_0_dataIn_data);
        gen_dout_splitCopy_0.dataIn_last(sig_gen_dout_splitCopy_0_dataIn_last);
        gen_dout_splitCopy_0.dataIn_ready(sig_gen_dout_splitCopy_0_dataIn_ready);
        gen_dout_splitCopy_0.dataIn_strb(sig_gen_dout_splitCopy_0_dataIn_strb);
        gen_dout_splitCopy_0.dataIn_valid(sig_gen_dout_splitCopy_0_dataIn_valid);
        gen_dout_splitCopy_0.dataOut_0_data(sig_gen_dout_splitCopy_0_dataOut_0_data);
        gen_dout_splitCopy_0.dataOut_0_last(sig_gen_dout_splitCopy_0_dataOut_0_last);
        gen_dout_splitCopy_0.dataOut_0_ready(sig_gen_dout_splitCopy_0_dataOut_0_ready);
        gen_dout_splitCopy_0.dataOut_0_strb(sig_gen_dout_splitCopy_0_dataOut_0_strb);
        gen_dout_splitCopy_0.dataOut_0_valid(sig_gen_dout_splitCopy_0_dataOut_0_valid);
        gen_dout_splitCopy_0.dataOut_1_data(sig_gen_dout_splitCopy_0_dataOut_1_data);
        gen_dout_splitCopy_0.dataOut_1_last(sig_gen_dout_splitCopy_0_dataOut_1_last);
        gen_dout_splitCopy_0.dataOut_1_ready(sig_gen_dout_splitCopy_0_dataOut_1_ready);
        gen_dout_splitCopy_0.dataOut_1_strb(sig_gen_dout_splitCopy_0_dataOut_1_strb);
        gen_dout_splitCopy_0.dataOut_1_valid(sig_gen_dout_splitCopy_0_dataOut_1_valid);
        hfe.din_data(sig_hfe_din_data);
        hfe.din_last(sig_hfe_din_last);
        hfe.din_ready(sig_hfe_din_ready);
        hfe.din_strb(sig_hfe_din_strb);
        hfe.din_valid(sig_hfe_din_valid);
        hfe.dout_data(sig_hfe_dout_data);
        hfe.dout_last(sig_hfe_dout_last);
        hfe.dout_ready(sig_hfe_dout_ready);
        hfe.dout_strb(sig_hfe_dout_strb);
        hfe.dout_valid(sig_hfe_dout_valid);
        hfe.headers_data(sig_hfe_headers_data);
        hfe.headers_last(sig_hfe_headers_last);
        hfe.headers_ready(sig_hfe_headers_ready);
        hfe.headers_strb(sig_hfe_headers_strb);
        hfe.headers_valid(sig_hfe_headers_valid);
        patternMatch.din_data(sig_patternMatch_din_data);
        patternMatch.din_last(sig_patternMatch_din_last);
        patternMatch.din_ready(sig_patternMatch_din_ready);
        patternMatch.din_strb(sig_patternMatch_din_strb);
        patternMatch.din_valid(sig_patternMatch_din_valid);
        patternMatch.match_data(sig_patternMatch_match_data);
        patternMatch.match_last(sig_patternMatch_match_last);
        patternMatch.match_ready(sig_patternMatch_match_ready);
        patternMatch.match_strb(sig_patternMatch_match_strb);
        patternMatch.match_valid(sig_patternMatch_match_valid);
    }
};