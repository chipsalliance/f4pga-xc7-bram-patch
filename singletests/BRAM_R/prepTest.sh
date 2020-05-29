# This is to test large memories (which will use BRAM_R sites) by filling them with all 1's.  It will be obvious if the FASM is incorrect.

D="128kb16"
SIZES="16 128k 131072"
# Generate the design, then patch the real.fasm with the contents of alt.mem to get an alt.fasm.  
# This is essentially what generate_tests.py does but this lets us put the results where we want and allows us to name the files what we want.
# Run them separated by && so if one or the other fails, this whole script will fail.
../../testing/generate_tests_script.sh . $SIZES  allones && python $MEM_PATCH_DIR/patch_mem.py $D/real.fasm $D/init/alt.mem $D/mapping.mdd $D/alt.fasm mem/ram
