#!/bin/bash
# Copyright (C) 2020-2021  The Project U-Ray Authors.
#
# Use of this source code is governed by a ISC-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/ISC
#
# SPDX-License-Identifier: ISC

export DESIGN_NAME=128b1
export SV_FILE_LOC=/home/nelson/mempatch/singletests/read3/128b1/vivado
export BATCH_DIR=/home/nelson/mempatch/singletests/read3/128b1


$XRAY_VIVADO -mode tcl

