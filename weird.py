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
