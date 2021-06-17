#!/bin/bash
# Copyright (C) 2020-2021  The Project U-Ray Authors.
#
# Use of this source code is governed by a ISC-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/ISC
#
# SPDX-License-Identifier: ISC

python $MEM_PATCH_DIR/run_tests.py 128b1

# The above line of code does essentially what the following would do:
# python $MEM_PATCH_DIR/run_tests.py 128b1/alt.fasm 128b1/init/init.mem 128b1/mapping.mdd 128b1/patched.fasm 128b1/real.fasm mem/ram
#
