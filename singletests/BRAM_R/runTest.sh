D="128kb16"
python $MEM_PATCH_DIR/run_tests.py $D/alt.fasm $D/init/init.mem $D/mapping.mdd $D/patched.fasm $D/real.fasm mem/ram
diff $D/patched.fasm $D/real.fasm
