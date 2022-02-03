#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

# File: fasm2init_all.py
# Author: Brent Nelson
# Created: 24 June 2020
# Description:
#    Driver to check all the designs in a directory for regression testing

import checkTheBits
import argparse
import pathlib
import fasm2init


def designSizes(designName):
    words = designName.split('b')[0]
    if words[-1] == 'k':
        words = int(words[:-1]) * 1024
    else:
        words = int(words)
    bits = int(designName.split('b')[1])
    return (words, bits)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "baseDir", help='Directory where design sub-directories are located.'
    )

    parser.add_argument("--verbose", action='store_true')

    parser.add_argument(
        "--printmappings", action='store_true', help='Print the mapping info'
    )

    args = parser.parse_args()

    baseDir = pathlib.Path(args.baseDir).resolve()
    dirs = list(baseDir.glob("*"))
    dirs.sort()

    for d in dirs:
        designName = d.name
        words, bits = designSizes(designName)
        fasm2init.fasm2init(
            d, "mem/ram", d / "{}.mdd".format(designName),
            d / "init/fromFasm.mem", d / "init/init.mem", d / "real.fasm",
            args.verbose, args.printmappings
        )

    print("")
