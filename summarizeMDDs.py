#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2020-2021  The SymbiFlow Authors.
#
# Use of this source code is governed by a ISC-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/ISC
#
# SPDX-License-Identifier: ISC

#
# Author: Brent Nelson
# Created: 15 June 2020
# Description:
#    Given a directory, will print out all the project names and their RAMB* primitives

import glob
import patch_mem
import parseutil.parse_mdd as mddutil


def main(dirs, verbose):
    for dr in dirs:
        fname = dr.split("/")[-1]
        if verbose:
            print("")
            print("Design is in: {}".format(dr))

        # Read the MDD data and filter out the ones we want for this memory
        mdd = dr + "/{}.mdd".format(fname)
        if verbose:
            print("Mdd is: {}".format(mdd))
        mdd_data = mddutil.read_mdd(mdd)
        for cell in mdd_data:
            print(
                "  {} {} {} ({}) {}:{} {}.{}".format(
                    fname,
                    cell.type,
                    cell.write_style,
                    cell.width,
                    cell.addr_end,
                    cell.addr_beg,
                    cell.slice_end,
                    cell.slice_beg,
                )
            )
        print("")


import argparse
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("baseDir")
    parser.add_argument("--verbose", action='store_true')
    args = parser.parse_args()
    print(args.baseDir)
    print(args.verbose)

    dirs = glob.glob(args.baseDir + "/*")
    main(dirs, args.verbose)
