#!/bin/bash
# Copyright (C) 2020-2021  The Project U-Ray Authors.
#
# Use of this source code is governed by a ISC-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/ISC
#
# SPDX-License-Identifier: ISC


if [ $# -ne 4 ] && [ $# -ne 5 ]; then 
    echo ""
    echo "    Usage: generate_tests_script.sh baseDir width depthName depth [ allones ]"
    echo ""
    exit 1
fi

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
echo "Done generating real.fasm"

# Do the alt.fasm file as well
python3 ${MEM_PATCH_DIR}/patch_mem.py $BATCH_DIR/real.fasm $BATCH_DIR/init/alt.mem $BATCH_DIR/$DESIGN.mdd $BATCH_DIR/alt.fasm mem/ram
echo "Done generating alt.fasm"
