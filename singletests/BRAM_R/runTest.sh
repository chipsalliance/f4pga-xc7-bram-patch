#!/bin/bash
# Copyright (C) 2020-2021  The Project U-Ray Authors.
#
# Use of this source code is governed by a ISC-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/ISC
#
# SPDX-License-Identifier: ISC

python $MEM_PATCH_DIR/run_tests.py 128kb16
diff 128kb16/patched.fasm 128kb16/real.fasm
