set_max_delay -from [get_cells -hier -filter {NAME =~ */gen_tx_cdcAFifo_0_inst/fifo_inst/r_gray_reg[*]*}] -to [get_cells -hier -filter {NAME =~ */gen_tx_cdcAFifo_0_inst/fifo_inst/r_gray_out_reg0_reg[*]*}] -datapath_only 5.000000
set_property ASYNC_REG TRUE [get_cells -hier -filter {NAME =~ */gen_tx_cdcAFifo_0_inst/fifo_inst/r_gray_out_reg0_reg[*]*}]
set_max_delay -from [get_cells -hier -filter {NAME =~ */gen_tx_cdcAFifo_0_inst/fifo_inst/r_gray_out_reg0_reg[*]*}] -to [get_cells -hier -filter {NAME =~ */gen_tx_cdcAFifo_0_inst/fifo_inst/r_gray_out_reg1_reg[*]*}] -datapath_only 5.000000
set_property ASYNC_REG TRUE [get_cells -hier -filter {NAME =~ */gen_tx_cdcAFifo_0_inst/fifo_inst/r_gray_out_reg1_reg[*]*}]
set_max_delay -from [get_cells -hier -filter {NAME =~ */gen_tx_cdcAFifo_0_inst/fifo_inst/r_bin_reg[*]*}] -to [get_cells -hier -filter {NAME =~ */gen_tx_cdcAFifo_0_inst/fifo_inst/r_gray_out_reg0_reg[*]*}] -datapath_only 5.000000
set_max_delay -from [get_cells -hier -filter {NAME =~ */gen_tx_cdcAFifo_0_inst/fifo_inst/w_gray_reg[*]*}] -to [get_cells -hier -filter {NAME =~ */gen_tx_cdcAFifo_0_inst/fifo_inst/w_gray_out_reg0_reg[*]*}] -datapath_only 5.000000
set_property ASYNC_REG TRUE [get_cells -hier -filter {NAME =~ */gen_tx_cdcAFifo_0_inst/fifo_inst/w_gray_out_reg0_reg[*]*}]
set_max_delay -from [get_cells -hier -filter {NAME =~ */gen_tx_cdcAFifo_0_inst/fifo_inst/w_gray_out_reg0_reg[*]*}] -to [get_cells -hier -filter {NAME =~ */gen_tx_cdcAFifo_0_inst/fifo_inst/w_gray_out_reg1_reg[*]*}] -datapath_only 5.000000
set_property ASYNC_REG TRUE [get_cells -hier -filter {NAME =~ */gen_tx_cdcAFifo_0_inst/fifo_inst/w_gray_out_reg1_reg[*]*}]
set_max_delay -from [get_cells -hier -filter {NAME =~ */gen_tx_cdcAFifo_0_inst/fifo_inst/w_bin_reg[*]*}] -to [get_cells -hier -filter {NAME =~ */gen_tx_cdcAFifo_0_inst/fifo_inst/w_gray_out_reg0_reg[*]*}] -datapath_only 5.000000
set_false_path -from [get_clocks -of [get_cells -hier -filter {NAME =~ */gen_tx_cdcAFifo_0_inst/fifo_inst/w_bin_reg[*]*}]] -to [get_cells -hier -filter {NAME =~ */gen_tx_cdcAFifo_0_inst/fifo_inst/r_reg_reg[*]*}]
set_max_delay -from [get_cells -hier -filter {NAME =~ */gen_rx_cdcAFifo_0_inst/fifo_inst/r_gray_reg[*]*}] -to [get_cells -hier -filter {NAME =~ */gen_rx_cdcAFifo_0_inst/fifo_inst/r_gray_out_reg0_reg[*]*}] -datapath_only 5.000000
set_property ASYNC_REG TRUE [get_cells -hier -filter {NAME =~ */gen_rx_cdcAFifo_0_inst/fifo_inst/r_gray_out_reg0_reg[*]*}]
set_max_delay -from [get_cells -hier -filter {NAME =~ */gen_rx_cdcAFifo_0_inst/fifo_inst/r_gray_out_reg0_reg[*]*}] -to [get_cells -hier -filter {NAME =~ */gen_rx_cdcAFifo_0_inst/fifo_inst/r_gray_out_reg1_reg[*]*}] -datapath_only 5.000000
set_property ASYNC_REG TRUE [get_cells -hier -filter {NAME =~ */gen_rx_cdcAFifo_0_inst/fifo_inst/r_gray_out_reg1_reg[*]*}]
set_max_delay -from [get_cells -hier -filter {NAME =~ */gen_rx_cdcAFifo_0_inst/fifo_inst/r_bin_reg[*]*}] -to [get_cells -hier -filter {NAME =~ */gen_rx_cdcAFifo_0_inst/fifo_inst/r_gray_out_reg0_reg[*]*}] -datapath_only 5.000000
set_max_delay -from [get_cells -hier -filter {NAME =~ */gen_rx_cdcAFifo_0_inst/fifo_inst/w_gray_reg[*]*}] -to [get_cells -hier -filter {NAME =~ */gen_rx_cdcAFifo_0_inst/fifo_inst/w_gray_out_reg0_reg[*]*}] -datapath_only 5.000000
set_property ASYNC_REG TRUE [get_cells -hier -filter {NAME =~ */gen_rx_cdcAFifo_0_inst/fifo_inst/w_gray_out_reg0_reg[*]*}]
set_max_delay -from [get_cells -hier -filter {NAME =~ */gen_rx_cdcAFifo_0_inst/fifo_inst/w_gray_out_reg0_reg[*]*}] -to [get_cells -hier -filter {NAME =~ */gen_rx_cdcAFifo_0_inst/fifo_inst/w_gray_out_reg1_reg[*]*}] -datapath_only 5.000000
set_property ASYNC_REG TRUE [get_cells -hier -filter {NAME =~ */gen_rx_cdcAFifo_0_inst/fifo_inst/w_gray_out_reg1_reg[*]*}]
set_max_delay -from [get_cells -hier -filter {NAME =~ */gen_rx_cdcAFifo_0_inst/fifo_inst/w_bin_reg[*]*}] -to [get_cells -hier -filter {NAME =~ */gen_rx_cdcAFifo_0_inst/fifo_inst/w_gray_out_reg0_reg[*]*}] -datapath_only 5.000000
set_false_path -from [get_clocks -of [get_cells -hier -filter {NAME =~ */gen_rx_cdcAFifo_0_inst/fifo_inst/w_bin_reg[*]*}]] -to [get_cells -hier -filter {NAME =~ */gen_rx_cdcAFifo_0_inst/fifo_inst/r_reg_reg[*]*}]
