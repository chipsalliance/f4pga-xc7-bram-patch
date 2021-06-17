#!/bin/bash
# Copyright (C) 2020-2021  The Project U-Ray Authors.
#
# Use of this source code is governed by a ISC-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/ISC
#
# SPDX-License-Identifier: ISC

echo "##########################################################################"
echo "Running: python bitMapping.py  testing/tests/master/1kb4 mem/ram 1kb4.mdd --printmappings | head -n 40"
python bitMapping.py  testing/tests/master/1kb4 mem/ram 1kb4.mdd --printmappings | head -n 5
echo "##########################################################################"
echo "Running: python fasm2init.py testing/tests/master/1kb4 mem/ram 1kb4.mdd --check"
python fasm2init.py testing/tests/master/1kb4 mem/ram 1kb4.mdd --check
echo "##########################################################################"
echo "Running: python checkTheBits.py testing/tests/master/2kb8 mem/ram"
python checkTheBits.py testing/tests/master/2kb8 mem/ram
echo "##########################################################################"
echo "Running: python genh.py testing/tests/master/1kb4/1kb4.mdd myDesign"
python genh.py testing/tests/master/1kb4/1kb4.mdd myDesign
cat myDesign.c | head -n 25
echo "##########################################################################"
