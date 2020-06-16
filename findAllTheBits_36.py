#
# Author: Brent Nelson
# Created: 15 June 2020
# Description:
#    Given a directory, will print out all the project names and their RAMB* primitives

import glob
import argparse
import findTheBits_36

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("baseDir")
    parser.add_argument("--verbose", action='store_true')
    parser.add_argument("--nomappings", action='store_true')
    args = parser.parse_args()
    print(args.baseDir)
    print(args.verbose)

    dirs = glob.glob(args.baseDir + "/*")
    findTheBits_36.findAllBitsInDirs(dirs, args.verbose, not args.nomappings)    
 


