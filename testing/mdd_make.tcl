proc getConsts { m } {
    set p [get_pins -of_objects $m -filter {DIRECTION == IN && NAME =~ "*ADDRA*"}]
    set vss []
    set gnds []
    foreach j $p {
        if { [lsearch [get_nets -of $j] *const1*] != -1 } {
            set vs [regsub "\\\["  [regsub "\\\]" $j " "] " " ]
            lappend vss "[lindex [split $vs] 1]"
        }
        if { [lsearch [get_nets -of $j] *const0*] != -1 } {
            set gnd [regsub "\\\["  [regsub "\\\]" $j " "] " " ]
            lappend gnds "[lindex [split $gnd] 1]"
        }
    }

    lsort -integer -decreasing $vss
    lsort -integer -decreasing $gnds

    set highOrder []
    set lowOrder []

    for {set i 13} {$i >= 0} {incr i -1} {
        if { [lsearch -exact $vss $i] >= 0 } {
            lappend highOrder 1
        } elseif { [lsearch -exact $gnds $i] >= 0 } {
            lappend highOrder 0
        } else {
            break
        }
    }

    for {set i 0} {$i < 14} {incr i 1} {
        if { [lsearch -exact $vss $i] >= 0 } {
            lappend lowOrder 1
        } elseif { [lsearch -exact $gnds $i] >= 0 } {
            lappend lowOrder 0
        } else {
            break
        }
    }

    # Now compute numerator for starting bits location
    set a $highOrder
    set x 0
    foreach n $a {
        set x [expr $x * 2]
        if { $n > 0 } {
            incr x
        }
    }
    set a $lowOrder
    set y 0
    foreach n $a {
        set y [expr $y * 2]
        if { $n > 0 } {
            incr y
        }
    }

    set lowOrder [lreverse $lowOrder]
    set dh [expr 1 << [llen $highOrder]]
    set dl [expr 1 << [llen $lowOrder]]
    return [list [list $x $dh $y $dl] $highOrder $lowOrder]
}



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
        set cp [getConsts $c]
        set cp [getConsts $c]
        set hinum [lindex [lindex $cp 0] 0]
        set hiden [lindex [lindex $cp 0] 1]
        set lonum [lindex [lindex $cp 0] 2]
        set loden [lindex [lindex $cp 0] 3]
        set hcp [lindex $cp 1]
        set lcp [lindex $cp 2]
        puts "  STARTINGOFFSET [expr 32768 * $hinum / $hiden]"
        set so [expr 32768 * $hinum / $hiden]
        puts $fp "  STARTINGOFFSET $so"
        puts "  HIGHCONSTPORTS \[ $hcp \]"
        puts $fp "  HIGHCONSTPORTS \[ $hcp \]"
        puts "  LOWCONSTPORTS \[ $lcp \]"
        puts $fp "  LOWCONSTPORTS \[ $lcp \]"
        puts "ENDCELL"
        puts $fp "ENDCELL"
    }
    close $fp

    puts "Done creating file $fname.mdd"
}
