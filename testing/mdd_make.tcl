proc mddMake {fname} {
    set props [list \
                   [list CELLTYPE REF_NAME] \
                   [list LOC LOC] \
                   [list MEM.PORTA.DATA_BIT_LAYOUT MEM.PORTA.DATA_BIT_LAYOUT] \
                   [list RTL_RAM_NAME RTL_RAM_NAME] \
                   [list RAM_EXTENSION_A RAM_EXTENSION_A] \
                   [list RAM_MODE RAM_MODE] \
                   [list READ_WIDTH_A READ_WIDTH_A] \
                   [list READ_WIDTH_B READ_WIDTH_B] \
                   [list WRITE_WIDTH_A WRITE_WIDTH_A] \
                   [list WRITE_WIDTH_B WRITE_WIDTH_B] \
                   [list RAM_OFFSET RAM_OFFSET]  \
                   [list BRAM_ADDR_BEGIN BRAM_ADDR_BEGIN] \
                   [list BRAM_ADDR_END BRAM_ADDR_END] \
                   [list BRAM_SLICE_BEGIN BRAM_SLICE_BEGIN] \
                   [list BRAM_SLICE_END BRAM_SLICE_END] \
                   [list RAM_ADDR_BEGIN RAM_ADDR_BEGIN] \
                   [list RAM_ADDR_END RAM_ADDR_END] \
                   [list RAM_SLICE_BEGIN RAM_SLICE_BEGIN] \
                   [list RAM_SLICE_END RAM_SLICE_END] \
                  ]

    if {$fname == ""} {
        set fp [open "[current_design].mdd" w]
    } else {
        set fp [open "$fname.mdd" w]
    }

    puts "DESIGN myDesign"
    puts $fp "DESIGN myDesign"
    puts "PART [get_parts -of  [current_design]]"
    puts $fp "PART [get_parts -of  [current_design]]"



    foreach c [get_cells * -hier -filter { REF_NAME == "RAMB18E1" || REF_NAME == "RAMB36E1" || REF_NAME == "RAMB18E2" || REF_NAME == "RAMB36E2"}] {
        puts "\nCELL $c"
        puts $fp "\nCELL $c"
        set tileaddr [get_tiles -of [get_bels -of $c]]
        puts "  TILE $tileaddr"
        puts $fp "  TILE $tileaddr"
        foreach p $props {
            set val [get_property [lindex $p 1] $c]
            if { $val == ""} { set val "NONE" }
            puts "  [lindex $p 0] $val"
            puts $fp "  [lindex $p 0] $val"
        }
        puts "ENDCELL"
        puts $fp "ENDCELL"
    }
    close $fp

    puts "Done creating file $fname.mdd"
}
