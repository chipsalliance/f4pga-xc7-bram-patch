#!/bin/bash
# Copyright (C) 2020-2021  The Project U-Ray Authors.
#
# Use of this source code is governed by a ISC-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/ISC
#
# SPDX-License-Identifier: ISC

# This is to test large memories (which will use BRAM_R sites) by filling them with all 1's.  It will be obvious if the FASM is incorrect.

# Generate the design, then patch the real.fasm with the contents of alt.mem to get an alt.fasm.  
# This is essentially what generate_tests.py does but this lets us put the results where we want and allows us to name the files what we want.
# Run them separated by && so if one or the other fails, this whole script will fail.
$MEM_PATCH_DIR/testing/generate_tests_script.sh . 16 128k 131072  allones
