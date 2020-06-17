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

An INIT line is a string and so the leftmost bit has index 0 in the string.  However, the nomenclature is like with Verilog: `...INIT_00[208:0]`, meaning that when read into a string, the MSB of the INIT data is on the left end.  So, the INIT strings must be swapped end for end so that the LSB of the initialization data is at index 0 in the INIT string.

The `MEM.PORTA.DATA_BIT_LAYOUT` entry tells how the data is spread between regular and parity bits.  Above for the 128b1 bit memory the entry is `p0_d1`, meaning that no bits are in the parity bits and 1 bit is in the data.  

There is also a READ_WIDTH_A value of 18 for the 128b1 design.  This means that the initialization data is broken up into 18 bit chunks of bits (we call such a chunk a "slice").  When a request is made to the memory 18 bits will be read and the rightmost bit will be used as the requested data (this is for a 128x1 bit memory after all) and returned.  That means if you go into the INIT and INITP strings you will see the following:
* The bits contained in the INITP lines are the top bits of the word (2 bits in the case of a read width of 18, 1 bit for a read width of 9, and so on).  The rest are in the INITlines.  In the case of 128b1 the parity bits are always 0 (and so wouldn't even be included in the FASM file).  In fact, the top 15 bits of the INIT slice and both parity bits in the INITP slice are fillers (0's).

So, with a little arithmetic you can compute where in an INIT line a particular bit from the memory initialize file will be.

## Step #3: Interleaved Bits - RAMB36E1
At this point it would seem we are done pretty easy - determine which INIT string contains the word of interest and then grab the bit.  

Not quite.  If both halves of a BRAM are used (when it is a RAMB36 instead of a RAMB18) then there are actually two set of INIT/INITP strings. Notice in the INIT strings above that there is as RAMB18_Y0 specified in the name?  That holds the even bits.  There is also a RAMB18_Y1 which olds the odd bits .  

If you zip together the Y0 and Y1 INIT and INITP strings into 512 character INIT and INITP strings, then the calculations are essentially identical for both RAMB18E1 and RAMB36E1 primitives.  The main differences are the lengths of the resulting INIT/INITP strings and some sizes are doubled.

## The findTheBits.py Program
The embodiment of the above algorithm is in the program `findTheBits.py`.  It is documented on the README.md page on the prjxray-bram-patch site.

Using `findTheBits.py` you can output the mapping that tells where, in the FASM INIT and INITP strings, each bit from a init.mem file can be found.

You can then further use that information and the prjxray database to convert those mappings to frame/bitoffset values in the actual bitstream.

## Reversing the Process
The mapping information from above can be used to map FASM INIT/INITP bits to init.mem values, meaning it can be _directly_ used to reconstruct an init.mem file from a bitstream (going through FASM as an intermediate step).

Or, the prjxray database information could be used to directly extract the bits from a bitstream, allowing you to bypass the FASM file step.

Read the `README.md` file on the prjxray-bram-patch github site for more information.
