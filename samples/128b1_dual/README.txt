This demonstrates multiple memories and hierarchy.  It was synthesized without the 
flatten hierarchy flag.  The MDD file gives the hierarchical name to
use in the "CELL" line and the rest in the "RTL_RAM_NAME".  So, a
name for one of the RAMs in this design to patch would be: "mem1/ram"
and the other would be "mem2/mem2a/ram" (you leave out the ram_reg part).

Test for this case:
    - Run Vivado and use selected commands from gen.tcl and make_mdd.tcl to generate results
    - To patch the first memory to create an alt.fasm do:  
        python patch_mem.py \
                'samples/128b1_dual/real.fasm' \
                'samples/128b1_dual/init/alt.mem' \
                'samples/128b1_dual/mapping.mdd' \
                '/tmp/alt.fasm' \
                'mem1/ram'
        - This will create /tmp/alt.fasm which where 'mem1/ram' has been patched with the 
          alt.mem init file ('mem2/mem2a/ram' is untouched).

    - To then test whether the tool can patch it back, do:
        python run_tests.py \
                '/tmp/alt.fasm' \
                'samples/128b1_dual/init/init.mem' \
                'samples/128b1_dual/mapping.mdd' \
                '/tmp/patched.fasm' \
                'samples/128b1_dual/real.fasm' \
                'mem1/ram'
        - This will patch /tmp/alt.fasm back to something which should be equivalent to /samples/128b1_dual/real.fasm
        - It will do the comparison and tell you if it worked

    - To test whether it can patch the second memory in this design, everything is the same except the mem to patch (last parameter)
      in each case is: 'mem2/mem2a/ram'.
