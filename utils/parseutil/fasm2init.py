from prjxray import fasm_disassembler
from prjxray.db import Database
import math
import sys
import os
import os.path
import fasm
import fasm.output
import utils.parseutil.parse_mdd as mddutil
import utils.parseutil.fasmread as fasmutil
import utils.parseutil.parse_init_test as initutil
import cProfile
from utils.parseutil.parse_mdd import Cell
from testing.random_memmaker import pad

import subprocess

from patch_mem import read_fasm

import sys
sys.path.append("D:\Research\prjxray\prjxray")


class Ramb36:
    def __init__(self, cell):
        self.mdd = cell
        self.unsorted_lines = set()
        self.tile = cell.tile
        if cell.type == "RAMB18E1":
            self.size = "18k"
        elif cell.type == "RAMB36E1":
            self.size = "36k"
        else:
            assert False
        self.has_pbits = (cell.pbits != '0')
        self.lines = []
        self.plines = []
        self.data = ""
        self.pdata = ""
        self.addr = (cell.addr_beg, cell.addr_end)
        self.slice = (cell.slice_beg, cell.slice_end)
        self.slicearr = ["" for x in range(1 + cell.addr_end - cell.addr_beg)]
        # assert len(data_for_cell) == cell.pbits + cell.dbits
        self.pwid = cell.pbits
        self.dwid = cell.dbits
        self.real_pwid = cell.pbits
        self.real_dwid = cell.dbits
        if cell.width > cell.pbits+cell.dbits:
            if cell.width < 9:
                self.real_pwid = 0
                self.real_dwid = cell.width
            elif cell.width < 72:
                self.real_pwid = cell.width % 8
                self.real_dwid = cell.width-self.real_pwid
            else:
                self.real_pwid = cell.width % 32
                self.real_dwid = cell.width-self.real_pwid

    def sort_lines(self):

        def reverse(string):
            string = string[::-1]
            return string
        serialized_data = ""
        serialized_pdata = ""
        if self.size == "36k":
            data = [['' for x in range(64)], ['' for x in range(64)]]
            pdata = [['' for x in range(8)], ['' for x in range(8)]]
            for line in self.unsorted_lines:
                tileaddr, y_val, initline = line.set_feature.feature.split('.')
                inittype, hexnum = initline.split('_')
                linenum = int(hexnum, 16)
                y = y_val[-1]
                bin_initline = '{:0>256}'.format(
                    bin(line.set_feature.value)[2:])
                bin_initline = reverse(bin_initline)
                if inittype == "INIT":
                    data[int(y)][linenum] = bin_initline
                else:
                    pdata[int(y)][linenum] = bin_initline
            comb_data = ["" for x in range(64)]
            comb_pdata = ["" for x in range(8)]
            for x in range(64):
                for y in range(256):
                    comb_data[x] = comb_data[x]+data[0][x][y]+data[1][x][y]
            for x in range(8):
                if len(pdata[0][x]) is not 0:
                    for y in range(256):
                        comb_pdata[x] = comb_pdata[x] + \
                            pdata[0][x][y]+pdata[1][x][y]
            data = comb_data
            pdata = comb_pdata
        else:
            assert self.size == "18k"
            data = ['' for x in range(64)]
            pdata = ['' for x in range(8)]
            for line in self.unsorted_lines:
                tileaddr, y_val, initline = line.set_feature.feature.split('.')
                inittype, hexnum = initline.split('_')
                linenum = int(hexnum, 16)
                bin_initline = '{:0>256}'.format(
                    bin(line.set_feature.value)[2:])
                bin_initline = reverse(bin_initline)
                if inittype == "INIT":
                    data[linenum] = bin_initline
                else:
                    pdata[linenum] = bin_initline

        for linenum, line in enumerate(data):
            print(f'{hex(linenum)}: {line}')
            if line == '':
                serialized_data = serialized_data+"{:0>256}".format(line)
            else:
                serialized_data = serialized_data+line
        for line in pdata:
            if line == '':
                serialized_pdata = serialized_pdata+"{:0>256}".format(line)
            else:
                serialized_pdata = serialized_pdata+line
        self.data = serialized_data
        self.pdata = serialized_pdata

        ########################################################################################################


def calc_wid(tiles):
    width = 0
    depth = 0
    for ramb36 in tiles.values():
        tile = ramb36.mdd
        if tile.slice_end >= width:
            width = tile.slice_end
    width = width+1
    return width




def extract_and_distribute_init(fasm=None, mdd=None, outfile=None, selectedMemToExtract=None):
    assert fasm is not None
    assert mdd is not None

    tmp_mdd_data = mddutil.read_mdd(mdd)
    if selectedMemToExtract is not None:
        mdd_data = [
            m for m in tmp_mdd_data
            if '/'.join(m.cell_name.split('/')[:-1]) + '/' +
            m.ram_name == selectedMemToExtract
        ]
    else:
        mdd_data = tmp_mdd_data
    if len(mdd_data) == 0:
        print(
            "No memories found in MDD file corresponding to {}, aborting.".
            format(selectedMemToExtract)
        )
        exit(1)

    print("Memories to be patched ({}):".format(len(mdd_data)))
    for l in mdd_data:
        print("  " + l.toString())
    print("")

    def distribute_lines(init_tups, tiles):
        for line in init_tups:
            tileaddr, y_val, initline = line.set_feature.feature.split('.')
            tiles[tileaddr].unsorted_lines.add(line)

    # Get all the FASM tuples
    fasm_tups = read_fasm(fasm)
    init_tups = fasmutil.get_init_data(tups=fasm_tups, mdd_data=mdd_data)
    tiles = {mdd.tile: Ramb36(mdd) for mdd in mdd_data}
    distribute_lines(init_tups=init_tups, tiles=tiles)
    for tile in tiles.values():
        tile.sort_lines()
    return tiles


def slice_n_dice(tiles, outfile=None):

    def reverse(string):
        string = string[::-1]
        return string

    addr_sets = set()
    slice_sets = set()
    width = 0
    depth = 0
    for ramb36 in tiles.values():
        tile = ramb36.mdd
        addr_sets.add((tile.addr_beg, tile.addr_end))
        slice_sets.add((tile.slice_beg, tile.slice_end))
        if tile.slice_end >= width:
            width = tile.slice_end
        if tile.addr_end >= depth:
            depth = tile.addr_end

    width = width+1
    depth = depth+1
    ordered_slices = sorted(list(slice_sets), key=lambda x: x[0], reverse=True)
    ordered_addrs = sorted(list(addr_sets), key=lambda x: x[0])
    inits = []
    addr_dict = {addr: [] for addr in ordered_addrs}
    for ramb36 in tiles.values():
        addr_dict[ramb36.addr].append(ramb36)
    for addr, mddlist in addr_dict.items():
        wid = 1 + addr[1] - addr[0]
        assert wid is not 0
        sortedmdd=sorted(mddlist, key=lambda x: x.slice[0], reverse=True)
        addr_dict[addr] = sortedmdd
        for mdd in sortedmdd:
            trimmed_pwid = mdd.pwid
            trimmed_dwid = mdd.dwid
            real_pwid = mdd.real_pwid
            real_dwid = mdd.real_dwid
            for x in range(len(mdd.slicearr)):
                p = mdd.pdata[x*real_pwid:(x+1)*real_pwid]
                d = mdd.data[x*real_dwid:(x+1)*real_dwid]
                p = reverse(p)
                d = reverse(d)
                mdd.slicearr[x] = '{}{}'.format(p, d)
        splicey = [''.join([mdd.slicearr[x] for mdd in sortedmdd])
                   for x in range(len(mdd.slicearr))]
        inits = inits + splicey
    hex_padwid = (int(width/4) if width % 4 == 0 else int(width/4)+1)
    vals = []
    for x in inits:
        if x == '':
            vals.append('0')
        else:
            vals.append(hex(int(x, 2))[2:])
    return vals


def export_init(val_list, outfile, width, depth):
    perline = 0
    if width == 1:
        perline = 256
    elif width <= 2:
        perline = 128
    elif width <= 4:
        perline = 64
    elif width <= 9:
        perline = 32
    elif width <= 18:
        perline = 16
    elif width <= 36:
        perline = 8
    elif width <= 72:
        perline = 4
    elif width <= 128:
        perline = 2
    else:
        perline = 1
    with open(outfile, 'w+') as f:
        vals = [val_list[x:x + perline] for x in range(0, depth, perline)]
        for val in vals:
            if len(val) is not 0:
                f.write(' '.join(val))
                f.write('\n')


def get_depth(design):
    if 'k' not in design:
        return int(design.split('b')[0])
    else:
        return 1028*int(design.split('k')[0])


def test_design(cwd,design):
    failed = os.path.join(cwd,'testing','failed_extraction.txt')
    success = os.path.join(cwd,'testing','succeeded_extraction.txt')
    testdir = os.path.join(cwd, "testing", "tests", "master", design)
    depth = get_depth(design)
    outfile = os.path.join(testdir, "extracted_init.mem")
    tiles = extract_and_distribute_init(fasm=os.path.join(testdir, "real.fasm"),
                                        mdd=os.path.join(
                                            testdir, "mapping.mdd"),
                                        outfile=outfile,
                                        selectedMemToExtract=None)
    width = calc_wid(tiles=tiles)
    val_list = slice_n_dice(tiles=tiles, outfile=outfile)
    export_init(val_list=val_list, outfile=outfile, width=width, depth=depth)
    real=os.path.join(testdir,'init','init.mem')
    print('Checking results...')
    diff = subprocess.run(
        ['diff', real, outfile],
        stdout=subprocess.PIPE,
        universal_newlines=True
    )

    if (diff.stdout == ''):
        print('RESULT: Files match, success!')
        with open(success,mode='a') as f:
            f.write('{}\n'.format(design))
        return "SUCCESS"
    else:
        print('RESULT: ERROR - Files do not match')
        with open(failed,mode='a') as f:
            f.write('{}\n'.format(design))
        return "FAILURE"
    return "SUCCESS"


def test_all_normal_designs():
    widths_to_test = [
        1, 2, 4, 8, 9, 16, 18, 32, 36, 64, 72, 128, 144, 256, 288
    ]
    depths_to_test = [
        '128', 
        '256', 
        '512', 
        '1k', 
        '2k',
        '4k', 
        '8k', 
        '16k',
        '32k', 
        '64k', 
        '128k'
    ]
    cwd = os.getcwd()
    failed = os.path.join(cwd,'testing','failed_extraction.txt')
    success = os.path.join(cwd,'testing','succeeded_extraction.txt')

    with open(failed, mode='w') as r:
        pass
    with open(success, mode='w') as r:
        pass
    for wid in widths_to_test:
        for depth in depths_to_test:
            design='{}b{}'.format(depth,wid)
            test_design(cwd=cwd,design=design)

def __main__():
    cwd = os.getcwd()
    failed = os.path.join(cwd,'testing','failed_extraction.txt')
    success = os.path.join(cwd,'testing','succeeded_extraction.txt')

    design = '16kb4'
    test_design(cwd=cwd,design=design)
    




if __name__ == "__main__":
    __main__()
