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

import parseutil.parse_mdd as mddutil
import parseutil.fasmread as fasmutil
import fasm
import pathlib

# from collections import recordclass

# Cases:
# overlapping addresses, different data slices
#   i.e. 16 bit wide broken into 0-3, 4-7, 8-11, 12-15
# different addresses, same data slices
#   i.e. 128kb1 with 0-32k, 32-64k, etc.
# wider address than real data


def pad(ch, wid, data):
    tmp = str(data)
    return (ch * (wid - len(tmp)) + tmp)


# Read the init file contents, pad to the desired width, and then reverse.
# That way, the LSB is element 0 of each word
def read_initfile(infile, wid, reverse=True):
    # Handles either Path or strings
    if isinstance(infile, pathlib.Path):
        infile = str(infile)

    with open(infile, 'r') as f:
        init_data = []
        for line in f:
            linedata = line.split(' ')
            for data in linedata:
                n = int(data, 16)
                data = bin(n)[2:]
                data = pad('0', wid, data)
                if reverse:
                    init_data.append(data[::-1])
                else:
                    init_data.append(data)
        return init_data


def initfile_to_initlist(infile, mdd):
    # Handles either Path or strings
    if isinstance(infile, pathlib.Path):
        infile = str(infile)

    width = mddutil.get_width(mdd)
    # print(width)
    with open(infile, 'r') as f:
        init_data = []
        for line in f:
            linedata = line.split(' ')
            for data in linedata:
                # data = f'{int(data,16):0{width}b}'
                # fluff the data but will be cut down later
                # try:
                #     data = int(data, 16)
                # except:
                #     print('heck')
                # data = f'{data:0{width}b}'
                # print(data)
                #TODO: Do you support both hex and binary here?
                #data2 = f'{int(data,16):0{width}b}'
                data = bin(int(data, 16))[2:]
                data = pad('0', width, data)
                #assert(data == data2)
                #print(data2)
                #print(data)
                # # # data = f'{bin(int(data,16))[2:]:0{width}}'
                # # # data = bin(int(data, 16))[2:]
                # # # if width is not None:
                # # #     data = data.zfill(width)
                init_data.append(data)
        return init_data


def initlist_to_edif_celldata(init, fasm_tups, mdd):
    # Foreach word of data in the mem.init file
    for bram_addr, data in enumerate(init):
        # Foreach cell in this memory
        for cell in mdd:
            # Is the word # within this cell's range?
            if bram_addr <= cell.addr_end and bram_addr >= cell.addr_beg:
                # Flip the data end for end (LSB on left)
                flip_data = data[::-1]
                # Get the bits for this word based on slice range
                data_for_cell = flip_data[cell.slice_beg:cell.slice_end + 1]
                # Flip those bits around
                data_for_cell = data_for_cell[::-1]
                # Did we get enough data?
                assert len(data_for_cell) == cell.pbits + cell.dbits
                actual_pbits = actual_dbits = 0
                # Is what we have just the right width for the word?
                if (cell.slice_end - cell.slice_beg) == cell.width:
                    actual_pbits = cell.pbits
                    actual_dbits = cell.dbits
                else:  # (cell.slice_end - cell.slice_beg) < cell.width:
                    # Need to pad on the left until we get the right width of word
                    wid = cell.width
                    data_for_cell = pad('0', wid, data_for_cell)
                    #data_for_cell2 = f'{data_for_cell:>0{wid}}'
                    #assert(data_for_cell == data_for_cell2)
                    # Here is the math to figure out how to break up the bits
                    #print("Cell.width = {}".format(wid))
                    if wid >= 9:
                        # Parity bits are what is left over from multiples of 8
                        actual_pbits = wid % 8
                        if wid >= 36:
                            actual_pbits = wid % 32
                            #print("Wid of {} is >= 36 so actual pbits is % 32".format(wid, actual_pbits))
                        actual_dbits = wid - actual_pbits
                        #print('Wid of {} is >=9 memories, actual_pbits = {} and actual_dbits = {}'.format(wid, actual_pbits, actual_dbits))
                    else:
                        actual_pbits = 0
                        actual_dbits = wid
                        #print('Wid of {} <9 memories so actual_pbits = {} and actual_dbits = {}'.format(wid, actual_pbits, actual_dbits))

                pbits = data_for_cell[0:actual_pbits]
                cell.INITP_LIST.append(pbits)
                # dbits = data_for_cell[actual_pbits:]
                # print(actual_dbits)
                dbits = data_for_cell[-actual_dbits:]
                cell.INIT_LIST.append(dbits)
                # print(f'{bram_addr} {len(dbits)} {dbits}')

    for cell in mdd:
        #print(len(cell.INIT_LIST))
        #print(len(cell.INITP_LIST))
        # assert len(cell.INIT_LIST) == 1 + cell.addr_end - cell.addr_beg
        cell.INIT = ''.join(cell.INIT_LIST[::-1])
        #print(f'{int(len(cell.INIT)/256)}')
        if cell.pbits > 0:
            cell.INITP = ''.join(cell.INITP_LIST[::-1])
    return mdd


def convert_placement(tileaddr):
    import re
    xyfind = re.compile(r'X(\d+)Y(\d+)')
    matched_addr = re.match(pattern=xyfind, string=tileaddr)
    assert matched_addr is not None
    x = matched_addr[1]
    y = matched_addr[2]
    tileaddr = 'BRAM_L_X{}Y{}'.format(x, y)
    #tileaddr2 = f'BRAM_L_X{x}Y{y}'
    #assert(tileaddr == tileaddr2)
    return tileaddr


def edif_celldata_to_fasm_initlines(mdd):
    def split_into_lines(bigstr):
        initlines = [
            ''.join(bigstr[x - 256:x]) for x in range(len(bigstr), 0, -256)
        ]
        return initlines

    tiles = {}
    for cell in mdd:
        # This is the routine that splits a RAMB36E1's data into Y0 and Y1 sections
        if cell.type == 'RAMB36E1':
            # This is the code that splits a RAMB36E1's data into Y0 and Y1 sections
            # Even elements go into Y1, odd elements go into Y0
            # print(f'{cell.type} IS a 36')
            y1_init = split_into_lines(cell.INIT[0::2])
            y0_init = split_into_lines(cell.INIT[1::2])
            y1_initp = split_into_lines(cell.INITP[0::2])
            y0_initp = split_into_lines(cell.INITP[1::2])
            tiledata = {
                'Y0': {
                    'INIT': y0_init,
                    'INITP': y0_initp
                },
                'Y1': {
                    'INIT': y1_init,
                    'INITP': y1_initp
                }
            }
            tileaddr = cell.tile
            tiles[tileaddr] = tiledata
        elif cell.type == 'RAMB18E1':
            # For a single-memory design (like .../master/128b1) the RAMB18E1 will always be in an even placement row,
            # which means it will be the Y0 data.
            # But, for multi-memory designs (like samples/128b1_dual), it may place one RAMB18E1 in an even placement row (Y0)
            # and a different (unrelated) one in an odd placement row (Y1).
            # Since we are only patching one memory at a time, we don't need to handle the case where both are being patched.
            # So, it is either Y0 or it is Y1, but not both.

            # print(f'{cell.type} isn\'t a RAMB36E1 apparently')
            y_init = split_into_lines(cell.INIT)
            y_initp = split_into_lines(cell.INITP)
            # Determine whether you are a Y0 or a Y1 memory
            row = int(cell.placement.split("Y")[1])
            if row % 2 == 0:
                half = 'Y0'
            else:
                half = 'Y1'
            tiledata = {half: {'INIT': y_init, 'INITP': y_initp}}
            tileaddr = cell.tile
            tiles[tileaddr] = tiledata
        else:
            print('Oh boy')
            raise Exception(
                'We don\'t know how to handle {}'.format(cell.type)
            )
    return tiles


def initlines_to_memfasm(initlines, infile_name):
    print(initlines)
    print("###")
    print(infile_name)
    fasmlines = []
    for tileaddr, tile in initlines.items():
        for yaddr, inits in tile.items():
            for init_type, data in inits.items():
                line_header = '{}.RAMB18_{}.{}_'.format(
                    tileaddr, yaddr, init_type
                )
                #line_header2 = f'{tileaddr}.RAMB18_{yaddr}.{init_type}_'
                #assert(line_header == line_header2)
                #print(str(len(data)) + "...")
                for count, data in enumerate(data):
                    if int(data) > 0:
                        # print(data)
                        while data[0] == '0':
                            data = data[1:]
                        datalen = len(data)
                        #count2 = count
                        count = hex(count)[2:].upper()
                        l = '{}{}[{}:0] = {}\'b{}'.format(
                            line_header, pad('0', 2, count), datalen - 1,
                            datalen, data
                        )
                        fasmlines.append(l)
                        #l2 = f'{line_header}{count2:02X}[{datalen-1}:0] = {datalen}\'b{data}'
                        #print(l)
                        #print(l2)
                        #assert(l == l2)
                        #fasmlines.append(
                        #    f'{line_header}{count:02X}[{datalen-1}:0] = {datalen}\'b{data}')
    memfasm = (next(fasm.parse_fasm_string(line)) for line in fasmlines)

    return memfasm


# This will create the new tuples needed from the infile
def initfile_to_memfasm(infile, fasm_tups, memfasm_name, mdd):
    # Read the init.mem file contents.
    init = initfile_to_initlist(infile, mdd=mdd)

    # Put the data for each BRAM into INIT data structures in each Cell record
    modified_mdd = initlist_to_edif_celldata(
        init=init, fasm_tups=fasm_tups, mdd=mdd
    )

    initlines = edif_celldata_to_fasm_initlines(mdd=modified_mdd)

    memfasm = initlines_to_memfasm(initlines, infile)
    # memfasm = [line for line in memfasm]
    # for line in memfasm:
    # print(type(line))
    # print(next(fasm.fasm_line_to_string(line)))
    return memfasm


def print_memfasm(memfasm):
    for mf in memfasm:
        print(type(mf))
        print(next(fasm.fasm_line_to_string(mf)))
