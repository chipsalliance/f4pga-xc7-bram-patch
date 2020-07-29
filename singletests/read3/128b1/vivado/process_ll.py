with open("test.ll") as f:
    lines = f.readlines()
    for lin in lines:
        tmp = lin.split()
        if len(tmp) != 6:
            continue
        if tmp[0] != "Bit":
            continue
        if tmp[4] != "Block=RAMB18_X0Y2":
            continue
        if "PARBIT" in lin:
            continue
        print(
            "{}\t{}\t{}\t{}".format(
                tmp[2],
                str(tmp[5].split(":")[1][3:]).rjust(8), tmp[3], tmp[1]
            )
        )
