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

# File: findTheBits_36.py
# Author: Brent Nelson
# Created: 15 June 2020
# Description:
#    Works for designs that use only RAMB35 primitives.
#    Will compute mapping from init.mem bit locations to FASM INIT/INITP lines/bits
#    Then will create feature name and find its mapping in segbits file from prjxray database
#    Finally, for each bits prints everything out
#    If a bit mismatch is found between a given init.mem file and locations in the FASM file, an assertion will fail.
#    So, you can run this and if no exceptions are thrown, all bits match

import glob
import patch_mem
import parseutil
import argparse
import findTheBits_xx
import pathlib


def pad(ch, wid, data):
    tmp = str(data)
    return (ch * (wid - len(tmp)) + tmp)


def findAllBitsInDir(dr, verbose, mappings, check):
    print("")
    print("Finding bits in directory: {}".format(str(dr)), flush=True)
    fname = dr.name
    # Read the MDD data and filter out the ones we want for this memory
    mdd_data = patch_mem.readAndFilterMDDData(
        str(dr / "{}.mdd".format(fname)), "mem/ram"
    )

    for cell in mdd_data:
        print(
            "  Processing cell: {} {} {}".format(
                cell.tile, cell.type, cell.placement
            ),
            flush=True
        )
        if cell.type == "RAMB36E1" or cell.type == "RAMB18E1":
            findTheBits_xx.findAllBits(
                dr, mdd_data, cell, str(dr / "init/init.mem"),
                str(dr / "real.fasm"), verbose, mappings, check
            )
        else:
            raise RuntimeError("Unknown cell.type: {}".format(cell.type))


def findAllBitsInDirs(dirs, verbose, mappings, check):
    for dr in dirs:
        findAllBitsInDir(dr, verbose, mappings, check)


# Must provide a baseDir argument
# The --mappings and --check args are independent.
# You can:
#    Just check for correctness (bits are where they should be in the FASM)
#    Write out the mapping strings to stdout
#    Do both
# But, doing neither doesn't do much of anything useful
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "baseDir", help='Directory where design sub-directories are located.'
    )
    parser.add_argument(
        "--design",
        help=
        'If provided, specify just which directory to process.  Otherwise, program will process all designs.'
    )
    parser.add_argument("--verbose", action='store_true')
    parser.add_argument(
        "--printmappings", action='store_true', help='Print the mapping info'
    )
    parser.add_argument(
        "--check",
        action='store_true',
        help='Check whether the bit matches the FASM file'
    )
    args = parser.parse_args()

    baseDir = pathlib.Path(args.baseDir)
    baseDir = baseDir.resolve()

    if args.design is not None:
        findAllBitsInDir(
            baseDir / args.design, args.verbose, args.printmappings, args.check
        )
    else:
        dirs = baseDir.glob("*")
        findAllBitsInDirs(dirs, args.verbose, args.printmappings, args.check)
    print("")
