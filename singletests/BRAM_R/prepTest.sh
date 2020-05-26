# This is to test large memories (which will use BRAM_R sites) by filling them with all 1's.  It will be obvious if the FASM is incorrect.

D="128kb16"
SIZES="16 128k 131072"
../../testing/generate_tests_script.sh . $SIZES  allones && python $MEM_PATCH_DIR/patch_mem.py $D/real.fasm $D/init/alt.mem $D/mapping.mdd $D/alt.fasm mem/ram
