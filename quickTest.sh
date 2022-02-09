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
