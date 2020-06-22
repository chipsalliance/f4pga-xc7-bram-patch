# 1. Overview
This software will take a bitstream and patch it with new memory contents to create a new bitstream.

More correctly, it will patch a .fasm file representing a bitstream to create a new .fasm file. 
It relies on prjxray to actually convert between .bit and .fasm representations.

It works on designs that have come from Vivado and relies on a Tcl script to extract the needed 
metadata (placed into a .mdd file) to understand which memory primitives in the bitstream correspond to which "chunks" 
of the original Verilog-specified memory.

Typically, the memory contents in Verilog are included using $readmemb() or
$readmemh() calls in Verilog to read the memory initialization contents from a text file. 
This flow expects that and will allow you to supply a different memory contents file. 
It will then patch that file contents into the BRAM primitives in the bitstream.

The tools relies on having a .mdd file to describe the contents of the memories in the 
compiled designs.  In a Vivado flow, the .mdd file can be created using the 
_testing/gen.tcl_ script.  For other flows, a mechanism will be needed to generate such files
from the tools in that other flow.

Since designs will typically have multiple BRAM-based memories, the tools expect the name of the 
memory to be patched to be specified.  The tool supports either hierarchical or flattened designs.

# 2. Installation

## 2.1 Linux, Python, and Vivado Versions
* At the current time, symbiflow/prjxray requires Vivado version 2017.2.  
* This tool was developed and has been tested on Ubuntu 16.04 with its native Python 3.5.

## 2.2 Installing prjxray and prjxray-bram-patch
After cloning both projects, follow the instructions on the prjxray github site for fully installing and configuring prjxray.  

There is nothing needed to be done to prjxray-bram-patch project once prjxray has been installed.

## 2.3 Startup Scripts
For running with Vivado, put in the following lines in your .bashrc file:

    # Adjust paths below as necessary
    export XRAY_VIVADO_SETTINGS=${HOME}/Xilinx_2017.2/Vivado/2017.2/settings64.sh
    source ${HOME}/prjxray/settings/artix7.sh
    
    export MEM_PATCH_DIR=${HOME}/prjxray-bram-patch

The first two lines are part of the prjxray installation.  The third line is required for prjxray-bram-patch and tells the tools where you installed it.   Note that you can run prjxray-bram-patch without Vivado installed --- the above is only included to be able to use Vivado to originally create designs.

## 2.4 Sample Designs and the Test Database
There are a few sample designs in the "samples" directory.

Additionally, a large collection of sample designs have been created and typically live in $MEM_PATCH_DIR/testing/tests/master.  
They are not needed for just doing patching but are used for testing of the patcher.  And, they are large and so are not included in the repo but can be recreated by running:

    python generate_tests.py

which will run through a series of memory sizes and generate test cases using Vivado and other scripts.  You can modify the contents of "generate_tests.py" to alter which memory sizes are generated.

In fact, generate_tests.py and the scripts it calls are instructive to show how a design is generated, along with its .mdd file.

NOTE: the above script will run for a LONG time.  But, you can go into the script and modify the list of the memory sizes it will generate test circuits for.


# 3. Test infrastructure
In order to verify that the patcher works for all size/shapes/configurations of memories, a test infrastructure is included.  The main two steps for this are (1) generation of tests and (2) the actual running of the tests.

## 3.1 Generation
This entails generating Verilog code which gets synthesized and implemented to a bitstream for each size of memory desired. 

### File: testing/generate_tests_script.sh
This script creates a single memory test case of ${DEPTH} words by ${WIDTH} bits wide.   The test case is placed into a directory: with the name ${DEPTH}b$WIDTH" and that directory is placed into a location specified by a parameter to this script.

1. It first creates the needed directory (referred to as _DIR_ in the discussion below).
1. It then creates two randomly-filled memory initialization files called DIR/init/init.mem and DIR/init/alt.mem
1. Next, it creates a customized SystemVerilog design in DIR/vivado which implements the memory and a top level design and which reads the memory's contents from DIR/init/init.mem.
1. Vivado is then called and the design is compiled through to bitstream.
1. The resulting bitstream is converted to a fasm file called: DIR/real.fasm
1. Finally DIR/real.fasm is patched with random data and written to DIR/alt.fasm (to be used in the testing later)

The above script can be called in a stand-alone fashion as:
```
generate_tests_script.sh someDirName 16 128k 131072 
```
and the results will be placed into `someDirName/128kb16`.  The results will consist of some memory initialization files, a .sv design and associated bit file, a .mdd file, and real.fasm and alt.fasm.

### File: generate_tests.py
This program is intended to generate and manage a large set of test designs (which it will place into `testing/tests/master`).  To do so it simply generates needed designs for all sizes by calling the program **testing/generate_tests_script.sh**.  The size of memories to generate designs for are given in a series of lists at the top of the code.  If a particular design already exists, then it will not re-generate it.
  
## 3.2 Testing
The program **run_tests.py** is used to actually do the testing.  The basic flow is as follows:
1. It keeps lists of tests that have (a) passed, (b) failed, or were (c) incomplete.
1. There is lots of flexibility provided to control which designs are tested:
   * There are lists to specify sizes and shapes of memories to test.
   * If the SKIP_PASSED flag is set to true, only those that have not yet passed will be tested.  
   * You can supply command line parameters to specify the files to patch and test or just the directory where they are located.  Otherwise, it will run tests on all designs in testing/tests/master that are not in its `testing/tests/passed.txt` file.  

Its basic operation is to patch the alt.fasm file with the contents of the init/init.mem file, writing the results into a patched.fasm file.  If the contents of patched.fasm match those of real.fasm the test is declared a success.

# 4. Doing a Simple Patch
You need not use the above test framework to do a simple patch.  The directory `singletests/simple` contains an example of a stand-alone test that creates a specific memory design and then tests whether it can re-patch it without error.  You might try running the `prepTest.sh` script followed by the `runTest.sh` script to see how this is done.  

## 4.1 Doing a Patch By Hand
Imagine that a design has been synthesized and implemented in Vivado.  The steps to patch its memory include the following:

#### Step 1: Generate .mdd File
While still in Vivado, do the following at the Tcl console:
```
source testing/mdd_make.tcl   # May need to adjust path
mddMake "original.mdd"
```
This will generate a .mdd file.  This file will contain the metadata needed to describe how the memory in the original design was broken up across a collection of BRAM cells.  

#### Step 2: Create New Memory Initialization File 
Based on the format of the original **$readmemb()** or **$readmemh()** file you used in your original Verilog, create a new memory initialization file to represent what you want the memory contents to be changed to.

At this point you should have the following files available (your filenames will be different):
    
    newMemContents.init
    original.bit
    original.mdd

#### Step 3: Generate a .fasm File From .bit File
Next, you convert your .bit file to a .fasm file using the following: 

    $XRAY_BIT2FASM original.bit > orig.fasm

#### Step 4: Patch the .fasm File
To replace the old memory contents in the bitstream with new contents, run the patch program using the following:

    python patch_mem orig.fasm newMemContents.init original.mdd patched.fasm memoryName

In the above, the last parameter is the name of the memory to be patched.  This name can be derived from a .mdd file.  For example, here is an .mdd file for a memory that is 128 bits deep by 16 bits wide:

    DESIGN design_1
    PART xc7a50tfgg484-1
    
    CELL mem/ram_reg
      TILE BRAM_L_X6Y20
      CELLTYPE RAMB18E1
      CELLPLACEMENT RAMB18_X0Y8
      MEM.PORTA.DATA_BIT_LAYOUT p0_d16
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
      BRAM_SLICE_END 15
      RAM_ADDR_BEGIN NONE
      RAM_ADDR_END NONE
      RAM_SLICE_BEGIN NONE
      RAM_SLICE_END NONE
    ENDCELL

The "memoryName" to provide when patching the design would be "mem/ram".  This is a combination of part of the CELL name (from the 1st line) and the RTL_RAM_NAME (from the 6th line).

In contrast, here is the top portion of a .mdd file for a hierarchical design containing multiple memories where the possible "memoryName" values to use would be either "mem1/ram" or "mem2/mem2a/ram".  As above you take all but the last component of the CELL value plus all of the RTL_RAM_NAME to create this.

DESIGN design_1
PART xc7a50tfgg484-1

```
CELL mem1/ram_reg
  TILE BRAM_L_X6Y5
  CELLTYPE RAMB18E1
  CELLPLACEMENT RAMB18_X0Y2
  MEM.PORTA.DATA_BIT_LAYOUT p0_d1
  RTL_RAM_NAME ram
  RAM_EXTENSION_A NONE

  ...
  
ENDCELL

CELL mem2/mem2a/ram_reg
  TILE BRAM_L_X6Y5
  CELLTYPE RAMB18E1
  CELLPLACEMENT RAMB18_X0Y3
  MEM.PORTA.DATA_BIT_LAYOUT p0_d1
  RTL_RAM_NAME ram
  RAM_EXTENSION_A NONE
  RAM_MODE TDP
  READ_WIDTH_A 18
```

Finally, here is a fragment from a file containing a large memory which has been broken up into a large array BRAM cells (it is from a 128K by 8 bit memory which was divided by Vivado into an array of 4 x 8  RAMB36E1 cells):

```
DESIGN design_1
PART xc7a50tfgg484-1

CELL mem/ram_reg_0_0
  TILE BRAM_L_X6Y30
  CELLTYPE RAMB36E1
  LOC RAMB36_X0Y6
  MEM.PORTA.DATA_BIT_LAYOUT p0_d1
  RTL_RAM_NAME ram
  RAM_EXTENSION_A LOWER
  ...
```
Because the memory has been broken up into many BRAM primitives the CELL values will have the form "mem/ram_reg_x_y" where the x and y values signify the primitive's position in the 2D tiling of BRAMs required to make up the large memory.

In this case the correct "memoryName" would be _mem/ram_.

From the above, it should be clear that the form of the name to use is the CELL value (minus the last component) concatenated with the RTL_RAM_NAME.

#### Step 5: Generate New .fasm File to New .bit File
Finally, you convert the new .fasm file to a .bit file using:

    $XRAY_FASM2FRAMES patched.fasm patched.frm \
      $XRAY_TOOLS_DIR/xc7frames2bit \
          --part_name $XRAY_PART \
          --part_file $XRAY_PART_YAML \
          --frm_file patched.frm \
          --output_file patched.bit

# 5. What Are MDD Files?
When large memories are created by the Vivado tools, they are chopped up and mapped onto a collection of BRAM primitives on the FPGA.  The patching tool requires information on how that mapping was done so that memory initialization file contents can be appropriately divided up for patching to the bitstream.  

The MDD file contains the information needed to do that mapping.  It is generated by the Tcl script: **testing/mdd_make.tcl**.  If you are not using Vivado, you will need to create such an MDD file some other way.

The current MDD file contains information on mapped BRAM primitives. It contains a number of BRAM properties that are not currently used and thus could possibly be reduced in the future.

# The findTheBits.py Program
The `findTheBits.py` program is intend to provide an understandable algorithm for computing the mapping between `init.mem` file bits and their location in the `INIT` and `INITP` strings in a FASM file.  

It then uses the prjxray database files to map those INIT and INITP bit locations to frame/offset locations in the real bitstream.  To do so it uses the `.../prjxray/database/artix7/segbits_bram_l.block_ram.db` file.

It then computes a mapping between those INIT and INITP string values and the bitstream's frames and bit offsets.  It does this using prjxray's `.../prjxray/database/artix7/segbits_bram_l.block_ram.db` file.

Additionally:
1. It can also check, bit-by-bit, if the mapping was correct by comparing bits in the `init.mem` file with bits in the FASM file's `INIT` strings.  If the check is successful it will print a message.
1. It has a verbose flag to help in debugging by printing out lots of information on how the mapping computation was done.

All of the 3 above options are controlled by command line options:

## Usage of findTheBits.py
It is intended, like all programs in this project, using the prjxray environment.  For all examples below, leaving off the `--design designName` argument will cause it to run for _all_ designs in the given directory (see last example).
```
# Run the program on a specific design.  
# If no assertion failures, then at least the program didn't crash. :-)
# Not a particularly useful mode
python findTheBits.py ./testing/tests/master --design 128b1

# Run the program on a specific design
# Check that the init.mem, FASM file, and bitstream file bit values match
python findTheBits.py ./testing/tests/master --design 128b1 --check

# Run the program on a specific design and print out the mappings
python findTheBits.py ./testing/tests/master --design 128b1 --printmappings

# Run the program on a specific design.
# Print out the mappings and do the checking
python findTheBits.py ./testing/tests/master --design 128b1 --printmappings --check

# Run the program and generate tons of debug output
python findTheBits.py ./testing/tests/master --design 128b1 --verbose

# Run the program on ALL designs in a given directory
# Will print out if the checks were succesful or will incur an asserter error
# Useful for regression tests
python findTheBits.py ./testing/tests/master --check
```

## Reversing the Process
The mapping information from above can be used to map bitstream bits to FASM INIT/INITP bits to init.mem values, meaning it can be _directly_ used to reconstruct an init.mem file from a bitstream (going through FASM as an intermediate step).

Or, the prjxray database information could be used to directly extract the bits from a bitstream, allowing you to bypass the FASM file step completely.

## More Info on findTheBits.py
Read the `The_Algorithm.md` file in this repo for more information on how memories are mapped to BRAMs and how the `findTheBits.py` program operates.


