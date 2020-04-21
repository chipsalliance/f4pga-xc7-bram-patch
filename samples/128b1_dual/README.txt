This demonstrates multiple memories and hierarchy and thus was
synthesized without the flatten hierarchy flag.  The MDD file gives
the hierarchical name to use in the "CELL" line and the rest in the
"RTL_RAM_NAME".  So, a name for one of the RAMs in this design to
patch would be: "mem1/ram" and the other would be "mem2/mem2a/ram"
(you leave out the ram_reg part).

To Build It:

  - Execute generate_test.sh in this directory.  It will generate .bit
    and .dcp files, the .mdd file, and a real.fasm file.

To Test It:
  - To patch the first memory to create an alt.fasm do:  
       python ../../patch_mem.py \
                'real.fasm' \
                'init/alt.mem' \
                'mapping.mdd' \
                '/tmp/alt.fasm' \
                'mem1/ram'

  - This will create /tmp/alt.fasm which is real.fasm but where
    'mem1/ram' has been patched with the alt.mem init file
    ('mem2/mem2a/ram' is untouched).

  - To then test whether the tool can patch it back, do:
       python ../../run_tests.py \
                '/tmp/alt.fasm' \
                'init/init.mem' \
                'mapping.mdd' \
                '/tmp/patched.fasm' \
                'real.fasm' \
                'mem1/ram'

  - This will patch /tmp/alt.fasm back to something which should be
    equivalent to /real.fasm It will also compare real.fasm with
    /tmp/patched.fasm do the comparison and tell you if it worked

  - To test whether it can patch the second memory in this design,
    everything is the same except the mem to patch (last parameter) in
    each case is: 'mem2/mem2a/ram'.  Since they are both 128b1
    memories, the same mem initialization files can be used.
