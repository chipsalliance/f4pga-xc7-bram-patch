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

# The runTest.sh script will run a single test against the design generated here.

# This script, however, will just patch 128b1/real.fasm with some new contents 
# (in this case it will patch 128b1/real.fasm with the contents of 128b1/init/alt.mem), 
# calling the result 128b1/new.fasm (and if you diff them it should match 128b1/alt.fasm due to the patching).

python $MEM_PATCH_DIR/patch_mem.py 128b1/real.fasm 128b1/init/alt.mem 128b1/mapping.mdd 128b1/new.fasm mem/ram

