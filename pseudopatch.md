Fasmpatch Pseudocode

Bit locations for a given value at index x of init value array:

find tiles from mdd where x is within address range
Untangling interleaved bits comes later, for now we will treat the bram as if it has 64 initlines if it is a ramb18 or 128 initlines if it is a ramb36

The bits of the init are to be divided among the slices. Since BRAM's are only able to accommodate certain data widths, these slices will be padded with 0's to the width indicated by width in the MDD
The bits contained in the INITP lines are the top bits of width (wid % 9), so for example if readwidth is 18, the top two bits would be in INITP and the bottom 16 would be located in INIT
This mapping is also indicated in by the MEM.PORTA.DATA_BIT_LAYOUT in the MDD, and will have a format like p2_d16
Determine the relative address by (x-addr_beg) and jump relative_addr*dwid up to the relavent chunk
    I usually end up ignoring the initlines of 256 bits by serializing them and then dividing them into chunks of the read width ascending
    so an array lines[linenum]=256'b ______ turns into slices[x] = 16'b _____ and sliceP[x] = 2'b __
The bits for the given slice of the init will be padded, but the relevant data is in the lower bit positions with their width given by (slice_end-slice_beg)

If tile is set to Ramb18 mode, you already have the bit position you want, but if the tile is Ramb36 mode, you will need to unentangle the init strings for each. The true 36k of the memory in this case is distributed with bit 0 going to y0, bit 1 going to y1, bit 2 going to y0, and so on. Once the lines have been returned to their y0 y1 orientations, you should know the tile, Y0/Y1, line, and bit number of any given bit from an initialization value.