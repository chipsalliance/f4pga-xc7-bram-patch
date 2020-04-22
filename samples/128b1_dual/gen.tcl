# parray env
# puts $::env(DESIGN_NAME)
create_project -force -part $::env(XRAY_PART) bigmem_test bigmem_test

#set_param general.maxBackupLogs 0
read_verilog -sv [glob vivado/*.sv]

synth_design -top top -flatten_hierarchy full

set_property CFGBVS VCCO [current_design]
set_property CONFIG_VOLTAGE 3.3 [current_design]
set_property BITSTREAM.GENERAL.PERFRAMECRC YES [current_design]
# set_param tcl.collectionResultDisplayLimit 0
set_property BITSTREAM.General.UnconstrainedPins {Allow} [current_design]

foreach site [get_sites -of [get_tiles -filter {TYPE == BRAM_R}]] {
  set_property PROHIBIT true $site
}

place_design
route_design

source ../../testing/mdd_make.tcl
mddMake ./mapping

write_edif -force ./vivado/${::env(DESIGN_NAME)}.edif
write_checkpoint -force ./vivado/${::env(DESIGN_NAME)}.dcp
write_bitstream -force ./vivado/${::env(DESIGN_NAME)}.bit

