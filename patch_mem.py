import sys
import os
import fasm
import fasm.output
import utils.parseutil.parse_mdd as mddutil
import utils.parseutil.fasmread as fasmutil
import utils.parseutil.parse_init_test as initutil
import cProfile
#from pathlib import Path

from prjxray.db import Database
from prjxray import fasm_disassembler

DIRECTORY = 'reconstruction_tests'


def main():
    # myargs = parse_args()
    # assert myargs.fasm is not None
    # assert myargs.init is not None
    # assert myargs.mdd is not None
    basedir = Path.cwd() / 'patch_test' / 'untested' / '128kb1'
    fasm_to_patch = basedir / 'alt.fasm'
    new_init = basedir / 'init' / 'init.mem'
    outfile = basedir / 'patched.fasm'
    mdd_fname = basedir / 'mapping.mdd'

    fasm_tups = read_fasm(fasm_to_patch)
    cleared_tups = fasmutil.clear_init(fasm_tups)
    mdd_data = mddutil.read_mdd(mdd_fname)
    memfasm = initutil.initfile_to_memfasm(
        infile=new_init,
        fasm_tups=fasm_tups,
        memfasm_name='temp_mem.fasm',
        mdd=mdd_data
    )
    merged = merge_tuples(cleared_tups=cleared_tups, mem_tups=memfasm)
    write_fasm(outfile, merged)
    print(
        'Patched\n  {}\nwith\n  {}\n  and wrote to\n{}'.format(
            fasm_to_patch, new_init, outfile
        )
    )


def patch_mem(fasm=None, init=None, mdd=None, outfile=None):
    assert fasm is not None
    assert init is not None
    assert mdd is not None

    # These are needed since these are paths and calling open() on them
    # in python3.5 gives an error.
    fasm = str(fasm)
    init = str(init)
    mdd = str(mdd)
    outfile = str(outfile)

    #    print('\nWorking Files:\n   fasm = {}\n   init = {}\n   mdd = {}\n   outfile = {}'.format(fasm, init, mdd, outfile))

    fasm_tups = read_fasm(fasm)
    cleared_tups = fasmutil.clear_init(fasm_tups)
    mdd_data = mddutil.read_mdd(mdd)
    memfasm = initutil.initfile_to_memfasm(
        infile=init,
        fasm_tups=fasm_tups,
        memfasm_name='temp_mem.fasm',
        mdd=mdd_data
    )
    # print("Running cProfile merge_tuples")
    # cProfile.run("merge_tuples(cleared_tups=cleared_tups, mem_tups=memfasm)")
    # print("Running normal merge_tuples")
    merged = merge_tuples(cleared_tups=cleared_tups, mem_tups=memfasm)
    write_fasm(outfile, merged)
    print("Patching done...")


def write_fasm(outfile, merged_tups):
    with open(outfile, 'w+') as out:
        out.write(fasm.fasm_tuple_to_string(merged_tups))


def merge_tuples(cleared_tups, mem_tups):
    db_path = os.getenv("XRAY_DATABASE_DIR")
    db_type = os.getenv("XRAY_DATABASE")
    db_path = os.path.join(db_path, db_type)
    db = Database(db_path, os.getenv("XRAY_PART"))
    grid = db.grid()
    if type(cleared_tups) is not list:
        cleared_tups = list(cleared_tups)
    if type(mem_tups) is not list:
        mem_tups = list(mem_tups)
    all_tups = fasmutil.chain_tuples(cleared_tups, mem_tups)
    merged = fasm.output.merge_and_sort(all_tups, sort_key=grid.tile_key)
    return merged


def read_fasm(fname):
    fasm_tuples = fasmutil.get_fasm_tups(fname)
    #TODO: Why are tiles being computed if not being used?
    tiles = fasmutil.get_in_use_tiles(fasm_tuples)
    tiles = fasmutil.get_tile_data(tups=fasm_tuples, in_use=tiles)
    return fasm_tuples


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(
        description='Alter BRAM initialization values'
    )
    parser.add_argument('-fasm', help="Fasm to be patched")
    parser.add_argument('-outfile', help="Output file")
    parser.add_argument('-init', help="New Init memory file used for patching")
    parser.add_argument(
        '-path',
        help="Path to directory in which patching is to take place",
        default=DIRECTORY
    )
    parser.add_argument(
        '-mdd', help="Filename for memory design description file"
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    assert len(sys.argv) == 5, \
           "Usage: patch_mem fasmFile newMemContents mddFile patchedFasmFile"
    patch_mem(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
