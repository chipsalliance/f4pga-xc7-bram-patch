#!/bin/bash

BASE_DIR=($1)
WIDTH=($2)
DEPTHNAME=($3)
DEPTH=($4)

if [ ! -z "$5" ]
  then
    ALLONES="allones"
  else
    ALLONES=""
fi

BATCH_DIR="${BASE_DIR}/${DEPTHNAME}b$WIDTH"
export BATCH_DIR=$BATCH_DIR
mkdir -p $BATCH_DIR
mkdir -p $BATCH_DIR/vivado
mkdir -p $BATCH_DIR/init

DESIGN="${DEPTHNAME}b${WIDTH}"
export DESIGN_NAME=$DESIGN
SV_FILE_LOC="$BATCH_DIR/vivado/$DESIGN.sv"
export SV_FILE_LOC

echo "BATCH_DIR" $BATCH_DIR
echo "DESIGN" $DESIGN

# Make two random memory init files, one for synthesis and one for use later in testing
python3 ${MEM_PATCH_DIR}/testing/random_memmaker.py $BATCH_DIR/init/init.mem $WIDTH $DEPTH $ALLONES # For Vivado
python3 ${MEM_PATCH_DIR}/testing/random_memmaker.py $BATCH_DIR/init/alt.mem $WIDTH $DEPTH     # For testing

# Make the top level design containing the memory
python3 ${MEM_PATCH_DIR}/testing/make_top.py $BATCH_DIR/vivado/$DESIGN.sv $WIDTH $DEPTH $BATCH_DIR/init/init.mem
echo "Done making top"

# Run Vivado to actually create the test design
echo `pwd`
$XRAY_VIVADO -mode batch -source ${MEM_PATCH_DIR}/testing/gen.tcl -log $BATCH_DIR/vivado/$DESIGN.log -journal $BATCH_DIR/vivado/$DESIGN.jou
echo "Done with Vivado"

# Convert its bitfile 
$XRAY_BIT2FASM $BATCH_DIR/vivado/$DESIGN.bit > $BATCH_DIR/real.fasm
echo "Done with bit2fasm"


