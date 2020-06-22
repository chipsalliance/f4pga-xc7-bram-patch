# Parses .bit files where it is a frame-by-frame structure (debug bitstream)
# This is for files that do a write to the FAR and then a write of FDRI data and then repeat
import pathlib

def parse_bit_file(bitFile, verbose=False):
    header_st = 0
    firstByte_st = 1
    secondByte_st = 2
    thirdByte_st = 3
    fourthByte_st = 4
    currentState = header_st
    # Use state machine to find sync word (0xAA995566).
    # Sync word marks the end of the header and the start of actual commands
    with bitFile.open('rb') as f:
        assert f is not None
        while currentState != fourthByte_st:
            byte = f.read(1)
            if currentState == header_st and ord(byte) == 0xAA:
                currentState = firstByte_st
            elif currentState == firstByte_st and ord(byte) == 0x99:
                currentState = secondByte_st
            elif currentState == secondByte_st and ord(byte) == 0x55:
                currentState = thirdByte_st
            elif currentState == thirdByte_st and ord(byte) == 0x66:
                currentState = fourthByte_st
            else:
                currentState = header_st
        return extract_frame_data(f, verbose)


def extract_frame_data(fd, verbose):
    frames = dict()
    while True:
        # Find type 1 write to FAR
        flg = lookFor3(
            fd, 0x30, 0x00, 0x20, 0x01, 0x30, 0x00, 0x40, 0x65, 0x30, 0x00,
            0x00, 0x01
        )
        if flg == 0:  # Set FAR
            bytes = fd.read(4)
            frameword = (bytes[0] << 24) | (bytes[1] << 16) | (bytes[2] <<
                                                               8) | bytes[3]
            if verbose:
                print("frameword = {}".format(hex(frameword)))
        elif flg == 1:  # Frame contents
            frmContents = []
            for i in range(101):
                bytes = fd.read(4)
                word = (bytes[0] << 24) | (bytes[1] << 16) | (bytes[2] <<
                                                              8) | bytes[3]
                frmContents.append(word)
            frames[frameword] = frmContents
        elif flg == 2:  # Skip CRC
            fd.read(4)
            frameword += 1
        else:
            break
    return frames


def lookFor3(f, b0, b1, b2, b3, b4, b5, b6, b7, b8, b9, ba, bb):
    #print("Looking for: {} {} {} {}".format(hex(str(b0)), hex(str(b1)),hex(str(b2)), hex(str(b3))))
    while (1):
        bytes = f.read(4)
        if len(bytes) < 4:
            return -1
        if bytes[0] == b0 and bytes[1] == b1 and bytes[2] == b2 and bytes[
                3] == b3:
            return 0
        elif bytes[0] == b4 and bytes[1] == b5 and bytes[2] == b6 and bytes[
                3] == b7:
            return 1
        elif bytes[0] == b8 and bytes[1] == b9 and bytes[2] == ba and bytes[
                3] == bb:
            return 2


def dumpframe(frames, frame, wordoffset=0, flen=101):
    print("frame #: " + hex(frame))
    f = frames[frame]
    for i in range(wordoffset, wordoffset + flen):
        w = f[i]
        print("  " + str(i) + " " + hex(w))


# Given a path will read the frame data into a data structure and return it.
# It is a dict where the keys are the frame numbers (integers) and the values are the 101 words of frame data in a list
# Later, this can be used to look up the individual values
def loadFrames(bitFile):
    return parse_bit_file(bitFile, False)


if __name__ == '__main__':
    bitfilePath = pathlib.Path("/home/nelson/mempatch/testing/tests/master/128b1/vivado/128b1.bit")
    frames = loadFrames(bitfilePath)

    dumpframe(frames, 0x00c0000f, 10, 10)
