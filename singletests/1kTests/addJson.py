import glob
import json

dirs = glob.glob("/home/nelson/mempatch/testing/tests/master/*")
dirs.sort()
s = "source /home/nelson/mempatch/testing/mdd_json_add.tcl\n"
for d in dirs:
    des = d.split("/")[-1]
    s += "cd {}\nopen_checkpoint vivado/{}.dcp\nmddMake\nclose_project\n".format(d, des)
print(s)
