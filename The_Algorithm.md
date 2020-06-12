# How to Find Bit Locations for a Given Value at Index x of Init Value Array

For purposes of this let's call the bit we want to be bit 'c' of word 'r' in our memory.  Example using Verilog syntax: mem[3][15] would have r=3, c=15.

## Organizaton of the `init.mem` File
The values in the file  are in ascending order starting with 0.  They may be either in binary or hex (a parameter in the tools).

## Step #1: Understand How Vivado Chopped a Big Memory Up into Many Smaller Memories
If a memory will fit, Vivado will pack it into a single BRAM.  But, if it won't fit, Vivado will break it up into multiple BRAM primitives.  In this latter case the MDD file tells what range of word addresses from within the original memory are contained within a given BRAM.  Here is an example from an MDD file:

```
MEM.PORTA.DATA_BIT_LAYOUT p0_d1
RTL_RAM_NAME ram
RAM_EXTENSION_A NONE
RAM_MODE TDP
READ_WIDTH_A 18
READ_WIDTH_B 18
WRITE_WIDTH_A 18
WRITE_WIDTH_B 18
RAM_OFFSET NONE
BRAM_ADDR_BEGIN 0
BRAM_ADDR_END 1023
BRAM_SLICE_BEGIN 0
BRAM_SLICE_END 0
```
This was for a 128b1 memory.  The `BRAM_ADDR_BEGIN` and `BRAM_ADDR_END` entries tell that this BRAM primitive contain words from 0 to 1023 (there are only 128 words in this design so they all fit into this primitive).  The `BRAM_SLICE_BEGIN` and `BRAM_SLICE_END` entries tell that bits 0 to 0 (the only bit) in each word is contained within this BRAM primitive.

Using this information you can determine whether the bit you are interested lies within this BRAM primitive.

## Step #2: Understanding How Bits Are Organized Within a Primitive
The initial contents of the BRAM are contained in INIT and INITP lines in the FASM file.
INIT lines have this form:
```
BRAM_L_X6Y5.RAMB18_Y0.INIT_00[208:0] = 209'b100000000000...
BRAM_L_X6Y5.RAMB18_Y0.INIT_01[240:0] = 241'b100000000000...
...
```
There are 256 bits in each INIT line.  Similarly, there are INITP lines that are 256 bits each.  They represent the parity bits contents.
A RAMB18 will have 64 INIT lines and 8 INITP lines giving a total of 18Kb of data while a  RAMB36 will have twice as many of each.

In an INIT line the leftmost bit is the **least significant** bit.  So, you need to mirror the bits left-to-right within INIT and INITP lines.  Once you do so the rightmost bit of an INIT_00 line is the LSB of the least significant word of the memory.

The `MEM.PORTA.DATA_BIT_LAYOUT` entry tells how the data is spread between regular and parity bits.  Above for the 128b1 bit memory the entry is `p0_d1`, meaning that no bits are in the parity bits and 1 bit is in the data.  

There is also a READ_WIDTH_A value of 18.  This means that the initialization data is broken up into 18 bit chunks (slices).  When a request is made to the memory 18 bits will be read and the rightmost bit will be used as the requested data (this is for a 128x1 bit memory after all) and returned.  That means if you go into the INIT and INITP strings you will see the following:
* The bits contained in the INITP lines are the top bits computed as `wid % 9`, so for example if readwidth is 18, the top two bits would be in INITP. And, in the case of 128b1 - the parity bits would always be 0 (and so wouldn't even be included in the FASM file)
* The INIT strings will contain 16 bit chunks (readwidth % of those bits will come from the main part of the memory and 2 of those bits will come from the parity part.  If you look in the INIT lines for the 128b1 memory you will see a pattern - the INIT line contains slices of either 16 0's in a row (a given data bit was 0) or 15 0's follow one 1 (a given data bit was a 1).  In each case there are 15 filler bits that are not needed and 1 bit of data.  NOTE: above you will see that not every INIT line has 256 bits - the reason is they don't include leading 0's.  So, to do this you would need to zero-pad on the left to get to 256 bits for an INIT and then reverse them left-to-right.

The reason for the padding is that BRAM's are only able to accommodate certain data widths (obviously their internal design imposes these limitations).  Thus, padding is used.

## Step #3: Interleaved Bits
At this point it would seem we are done pretty easy - determine which INIT string contains the word of interest and then grab it.  Not quite.  If both halves of a BRAM are used (it is a RAMB36 instead of a RAMB18) then there are actually two RAMB18's and their bits are interleaved.  Notice in the INIT strings above that there is as RAMB18_Y0 specified in the name?  That is bottom RAMB18.  There is also a RAMB18_Y1.  Even bits are in the bottom half and odd bits are in the top half.  So the LSB of RAMB18_Y0.INIT_00 wll be bit 0 and the LSB of RAMB18_Y1_INIT will be bit 1.  Just what does that mean?

Determine the relative address by (x-addr_beg) and jump relativeaddr*dwid up to the relavent chunk
    I usually end up ignoring the initlines of 256 bits by serializing them and then dividing them into chunks of the read width ascending
    so an array lines[linenum]=256'b __ turns into slices[x] = 16'b __ and sliceP[x] = 2'b __
The bits for the given slice of the init will be padded, but the relevant data is in the lower bit positions with their width given by (slice_end-slice_beg)

If tile is set to Ramb18 mode, you already have the bit position you want, but if the tile is Ramb36 mode, you will need to unentangle the init strings for each. The true 36k of the memory in this case is distributed with bit 0 going to y0, bit 1 going to y1, bit 2 going to y0, and so on. Once the lines have been returned to their y0 y1 orientations, you should know the tile, Y0/Y1, line, and bit number of any given bit from an initialization value.
Here's a little summary I whipped up of the mapping of bits from a memory initialization file to actual tile, initline, and bit numbers inside a fasm file