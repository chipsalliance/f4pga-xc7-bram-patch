#!/bin/bash

export DESIGN="128b1_dual"
export DESIGN_NAME=$DESIGN

if [[ ! -d init ]]; then mkdir init; fi

# Make two random memory init files, one for synthesis and one for use later in testing
python3 ../../testing/random_memmaker.py init/init.mem 1 128    # For Vivado
python3 ../../testing/random_memmaker.py init/alt.mem 1 128     # For testing

# Make the top level design containing the memory
# Run Vivado to actually create the test design
echo `pwd`
$XRAY_VIVADO -mode batch -source gen.tcl -log vivado/$DESIGN.log -journal vivado/$DESIGN.jou
echo "Done with Vivado"

# Convert its bitfile 
$XRAY_BIT2FASM vivado/$DESIGN.bit > real.fasm
echo "Done with bit2fasm"
