# prjxray-bram-patch

This software will take a bitstream and patch it with new memory contents to create a new bitstream.

More correctly, it will patch a .fasm file representing a bitstream to create a new .fasm file. 
It relies on prjxray to actually convert between .bit and .fasm representations.

It works on designs that have come from Vivado and relies on a Tcl script to extract the needed 
metadata to understand which memory primitives in the bitstream correspond to which "chunks" 
of the original Verilog-specified memory.

As written, the tool expects that the design was originally described in HDL and 
compiled using Vivado. Typically, the memory contents in Verilog are included using $readmemb() 
$readmemh() call in Verilog to read the memory initialization contents from a text file. 
This flow expects that and will allow you to supply a different memory contents file. 
It will then patch that file contents into the BRAM primitives in the bitstream.

See the wiki here for requirements, installation, usage, and testing instructions.

