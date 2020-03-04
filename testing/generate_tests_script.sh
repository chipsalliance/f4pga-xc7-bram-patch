#!/bin/bash

WIDTH=($1)
DEPTHNAME=($2)
DEPTH=($3)

cd testing
mkdir -p tests
mkdir -p tests/master

BATCHDIR="tests/master/${DEPTHNAME}b$WIDTH"
export BATCH_DIR=$BATCHDIR
mkdir -p $BATCHDIR
mkdir -p $BATCHDIR/vivado
mkdir -p $BATCHDIR/init

DESIGN="${DEPTHNAME}b${WIDTH}"
export DESIGN_NAME=$DESIGN
SV_FILE_LOC="$BATCHDIR/vivado/$DESIGN.sv"
export SV_FILE_LOC
echo "BATCHDIR" $BATCHDIR
echo "DESIGN" $DESIGN

python3 random_memmaker.py $BATCHDIR/init/init.mem $WIDTH $DEPTH 
python3 random_memmaker.py $BATCHDIR/init/alt.mem $WIDTH $DEPTH 

python3 make_top.py $BATCHDIR/vivado/$DESIGN.sv $WIDTH $DEPTH $BATCHDIR/init/init.mem
echo "Done making top"

echo `pwd`
$XRAY_VIVADO -mode batch -source gen.tcl -log $BATCHDIR/vivado/$DESIGN.log -journal $BATCHDIR/vivado/$DESIGN.jou
echo "Done with Vivado"

$XRAY_BIT2FASM $BATCHDIR/vivado/$DESIGN.bit > $BATCHDIR/real.fasm


