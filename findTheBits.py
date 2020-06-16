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

import sys
import os
import glob
import json
import patch_mem
import parseutil
import parseutil.parse_mdd as mddutil
import parseutil.fasmread as fasmutil
import fasm
import argparse
import findTheBits_36
import findTheBits_18


def pad(ch, wid, data):
    tmp = str(data)
    return (ch * (wid - len(tmp)) + tmp)

def findAllBitsInDir(dr, verbose, mappings):
    print("\nFinding bits in directory: "  + dr, flush = True)
    fname = dr.split("/")[-1]
    print(dr)
    # Read the MDD data and filter out the ones we want for this memory
    mdd_data = patch_mem.readAndFilterMDDData(dr + "/{}.mdd".format(fname), "mem/ram")
    for cell in mdd_data:
        print("  Processing cell: {} {} {}".format(cell.tile, cell.type, cell.placement), flush = True)
        if cell.type == "RAMB36E1":
            findTheBits_36.findAllBits(dr, mdd_data, cell, verbose, mappings)
        elif cell.type == "RAMB18E1":
            findTheBits_18.findAllBits(dr, mdd_data, cell, verbose, mappings)

def findAllBitsInDirs(dirs, verbose, mappings):
    dirs.sort()
    for dr in dirs:
        findAllBitsInDir(dr, verbose, mappings)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("baseDir", help='Directory where design sub-directories are located.')
    parser.add_argument("--design", help='If provided, specify just which directory to process.  Otherwise, program will process all designs.')
    parser.add_argument("--verbose", action='store_true')
    parser.add_argument("--nomappings", action='store_true')
    
    args = parser.parse_args()


    if args.design is not None:
        findAllBitsInDir(args.baseDir + "/" + args.design, args.verbose, not args.nomappings)
    else:
        dirs = glob.glob(args.baseDir + "/*")
        findAllBitsInDirs(dirs, args.verbose, not args.nomappings)
    print("")
