#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2020-2021  The Project U-Ray Authors.
#
# Use of this source code is governed by a ISC-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/ISC
#
# SPDX-License-Identifier: ISC

#
# Author: Brent Nelson
# Created: 18 Dec 2020
# Description:
#    Given a directory, will analyze all the MDD files

import glob
import patch_mem
import parseutil.parse_mdd as mddutil
from collections import namedtuple

Mdd = namedtuple('Mdd', 'typ width addrbeg addrend')

def main(dirs, verbose):
    d = dict()
    for dr in dirs:
        fname = dr.split("/")[-1]
        if verbose:
            print("")
            print("Design is in: {}".format(dr))

        # Read the MDD data and filter out the ones we want for this memory
        mdd = dr + "/mapping.mdd".format(fname)
        if verbose:
            print("Mdd is: {}".format(mdd))
        mdd_data = mddutil.read_mdd(mdd)
        for cell in mdd_data:
          if not fname in d:
            print("Creating entry for " + fname)
            d[fname] = []
          d[fname].append(Mdd(typ=cell.type, width=cell.width, addrbeg=cell.addr_beg, addrend=cell.addr_end))
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

    def printMdd(fname, mdd):
      print("fname = {}, mdd = ".format(fname))
      for elmt in mdd:
        print("    {}".format(elmt))

    #for fname, mdd in d.items():
    #  printMdd(fname, mdd)

    # Now check that all widths are the same
    print("Checking widths:")
    for fname, mdd in d.items():
      wid = mdd[0].width
      for elmt in mdd:
        if wid != elmt.width:
          printMdd(fname, mdd)

    print("Checking depths:")
    for fname, mdd in d.items():
      depth = mdd[0].addrend - mdd[0].addrbeg
      for elmt in mdd:
        if depth != elmt.addrend - elmt.addrbeg:
          printMdd(fname, mdd)




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
