# parray env
# puts $::env(DESIGN_NAME)
create_project -force -part $::env(XRAY_PART) bigmem_test /tmp/bigmem_test

#set_param general.maxBackupLogs 0
read_verilog $::env(SV_FILE_LOC)

synth_design -top top -flatten_hierarchy full

set_property CFGBVS VCCO [current_design]
set_property CONFIG_VOLTAGE 3.3 [current_design]
set_property BITSTREAM.GENERAL.PERFRAMECRC YES [current_design]
# set_param tcl.collectionResultDisplayLimit 0
set_property BITSTREAM.General.UnconstrainedPins {Allow} [current_design]

place_design
route_design

source ${::env(MEM_PATCH_DIR)}/testing/mdd_make.tcl
mddMake ${::env(BATCH_DIR)}/mapping

write_edif -force ${::env(BATCH_DIR)}/vivado/${::env(DESIGN_NAME)}.edif
write_checkpoint -force ${::env(BATCH_DIR)}/vivado/${::env(DESIGN_NAME)}.dcp
write_bitstream -raw_bitfile -logic_location_file -readback_file  -bin_file -force ${::env(BATCH_DIR)}/vivado/${::env(DESIGN_NAME)}.bit

