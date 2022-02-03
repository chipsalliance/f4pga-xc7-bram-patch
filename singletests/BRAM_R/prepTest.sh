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

# This is to test large memories (which will use BRAM_R sites) by filling them with all 1's.  It will be obvious if the FASM is incorrect.

# Generate the design, then patch the real.fasm with the contents of alt.mem to get an alt.fasm.  
# This is essentially what generate_tests.py does but this lets us put the results where we want and allows us to name the files what we want.
# Run them separated by && so if one or the other fails, this whole script will fail.
$MEM_PATCH_DIR/testing/generate_tests_script.sh . 16 128k 131072  allones
