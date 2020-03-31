import fasm
import fasm.output
import re
from itertools import chain


def get_in_use_tiles(tups):
    tiles = []
    for tup in tups:
        if tup.set_feature:
            tup = tup.set_feature
            if 'IN_USE' in tup.feature:
                if tup.feature[0:4] == 'BRAM':
                    # print(fasm.set_feature_to_str(tup))
                    tiles.append(tup)
    return tiles


def get_tile_data(tups, in_use):
    tiles = dict()
    for tiletup in in_use:
        #tileaddr = '.'.join(tiletup.feature.split('.')[0:1])
        tileaddr = '.'.join(tiletup.feature.split('.')[0:2])
        tiles[tileaddr] = []
        for fasmtup in tups:
            if tileaddr in fasmtup.set_feature.feature:
                tiles[tileaddr].append(fasmtup.set_feature)
    return tiles


def get_fasm_tups(fname):
    fasm_tuples = [tup for tup in fasm.parse_fasm_filename(fname)]
    return fasm_tuples


def memShouldBeIncluded(tile, memType, half, mdd_data):
    for m in mdd_data:
        if m.tile == tile:
            if m.type == "RAMB36E1":
                return True
            elif m.type == "RAMB18E1":
                row = int(m.placement.split("Y")[1])
                if half == "Y0" and row % 2 == 0:
                    #print("True Y0: {} {} {} {}".format(tile, memType, half, row))
                    return True
                elif half == "Y1" and row % 2 == 1:
                    #print("True Y1: {} {} {} {}".format(tile, memType, half, row))
                    return True
            else:
                raise Exception("Unknown MDD memory type: {}".format(m.type))
    return False


# Get all the INIT for BRAM tuples that map to the MDD memory to patch
def get_init_data(tups, mdd_data, get_initp_too=True):
    # init_boi = re.compile(
    #     r"(BRAM_[LR]_X\d+Y\d+)\.(RAMB\d\d_Y\d+)\.((INIT(P)?_[0-9a-fA-F]{2})(\[\d+(:\d+)?\]))")
    # if not get_initp_too:
    init_boi = re.compile(
        r"((BRAM_[LR]_X\d+Y\d+)\.(RAMB\d\d_Y\d+)\.((INIT(P)?_)[0-9a-fA-F]{2})(\[\d+(:\d+)?\])?)"
    )
    inits = set()
    for tup in tups:
        feature = tup.set_feature.feature
        if re.match(pattern=init_boi, string=feature):
            inits.add(tup)
    return inits


def clear_init(tups):
    init = get_init_data(tups)
    cleared_tups = {tup for tup in tups if tup not in init}
    return fasm.output.merge_and_sort(cleared_tups)


def chain_tuples(main_tuples, secondary_tuples):
    all_tuples = chain(main_tuples, secondary_tuples)
    for item in all_tuples:
        yield item


# gets those good sorted tiles
def get_sorted_tiles(tups):
    in_use = re.compile(r'BRAM_[LR]_X\d+Y\d+\.RAMB18_Y(\d)\.IN_USE')
    tiles = []
    for tup in tups:
        feature = tup.set_feature.feature
        if re.match(pattern=in_use, string=feature):
            tilename = get_tup_tileaddr(tup)
            tiles.append(tilename)
    print('Unsorted')
    for tile in tiles:
        print(tile)
    print('Sorted')
    tiles = sorted(tiles, reverse=True)
    for tile in tiles:
        print(tile)
    return tiles


def get_sorted_tiledata(tups):
    tiles = get_sorted_tiles(tups)
    tiledict = {}
    for tile in tiles:
        tiledict[tile] = set()
    for tup in tups:
        tileaddr = get_tup_tileaddr(tup)
        if tileaddr in tiledict.keys():
            tiledict[tileaddr].add(tup)
    return tiledict


def get_tup_tileaddr(tup):
    tilename = '.'.join(tup.set_feature.feature.split('.')[0:2])
    return tilename


def get_rw_widths(tiles=None, tups=None):
    if tups:
        tiles = get_sorted_tiledata(tups)
    rw_check = re.compile(
        r'BRAM_[LR]_X\d+Y\d+\.RAMB18_Y\d\.(?:READ|WRITE)_WIDTH_[AB]_(?P<wid>\d+)'
    )
    for tileaddr, tilelines in tiles.items():
        widths = set()
        for line in tilelines:
            widmatch = re.match(
                pattern=rw_check, string=line.set_feature.feature
            )
            if widmatch:
                widths.add(int(widmatch.group('wid')))
        if len(widths) > 1:
            for wid in widths:
                print(wid)
            tiles[tileaddr] = 0
        else:
            for wid in widths:
                tiles[tileaddr] = wid
    return tiles
