import sys
import os
import fasm
import fasm.output
import parseutil.parse_mdd as mddutil
import parseutil.fasmread as fasmutil
import parseutil.parse_init_test as initutil
import cProfile
import pathlib

from prjxray.db import Database
from prjxray import fasm_disassembler


def patch_mem(
    fasm=None,
    init=None,
    mdd=None,
    outfile=None,
    selectedMemToPatch=None,
    verbose=False,
    partial=False
):
    assert fasm is not None
    assert init is not None
    assert mdd is not None
    assert selectedMemToPatch is not None

    mdd_data = mddutil.readAndFilterMDDData(mdd, selectedMemToPatch, verbose)

    # Get all the FASM tuples
    fasm_tups = read_fasm(fasm)

    # Get everything BUT the INIT ones selected for patching
    cleared_tups = fasmutil.clear_init(fasm_tups, mdd_data)

    # Create the new tuples from initfile contents
    memfasm = initutil.initfile_to_memfasm(
        infile=init,
        fasm_tups=fasm_tups,
        memfasm_name='temp_mem.fasm',
        mdd=mdd_data
    )

    if partial == True:
        # Find any and all non-INIT tuples located at the patched BRAM
        frame_tups = []
        for data in mdd_data:
            for tup in cleared_tups:
                if tup[0] != None and tup.set_feature.feature.find(data.tile
                                                                   ) != -1:
                    frame_tups.append(tup)
        # Merge the newly found non_INIT tuples located at the BRAM with the
        # new memory tuples to create a partial FASM file
        merged = merge_tuples(cleared_tups=frame_tups, mem_tups=memfasm)
        write_fasm(outfile, merged)
    else:
        # Merge all non-INIT tuples (cleared_tups) in with the new memory tuples
        # to create a new complete FASM file
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


if __name__ == "__main__":
    if len(sys.argv) == 6:
        patch_mem(
            sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
        )
    elif len(sys.argv) == 7 and sys.argv[6] == "--partial":
        if sys.argv[6] == "--partial":
            patch_mem(
                sys.argv[1],
                sys.argv[2],
                sys.argv[3],
                sys.argv[4],
                sys.argv[5],
                partial=True
            )
        elif sys.argv[6] == "--verbose":
            patch_mem(
                sys.argv[1],
                sys.argv[2],
                sys.argv[3],
                sys.argv[4],
                sys.argv[5],
                verbose=True
            )
        else:
            print(
                "Usage: patch_mem fasmFile newMemContents mddFile patchedFasmFile memName [--verbose] [--partial]"
            )
    elif len(sys.argv) == 8:
        patch_mem(
            sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5],
            True, True
        )
    else:
        print(
            "Usage: patch_mem fasmFile newMemContents mddFile patchedFasmFile memName [--verbose] [--partial]"
        )
