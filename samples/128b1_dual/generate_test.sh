#!/bin/bash
# Copyright 2020-2022 F4PGA Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0


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
