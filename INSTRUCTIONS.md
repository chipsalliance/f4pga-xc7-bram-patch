1. The old designs are not longer valid with this version of the code.  So, re-generate some new ones.   Depths of up to 32K and widths up to 72 would be a good place to start.
1. Start by experimenting with bitMapping.py to understand how the bitmapping process works.  Read the comments at both top and bottom of the file.
1. Once you are comfortable with that, move on to fasm2init.py.  It has much of the code needed (but not quite all) for a bits2init.py program.
1. Finally, look at checkTheBits.py.  The interesting lines are: 61-67 where it reads a bitstream and lines 104-111 where it pulls an individual bit out of a bitstream frame.  

Before proceeding you should be comfortable running all 3 programs above and understand basically what they do.

The bits2init.py program is most like fasm2init.py but uses the noted pieces from checkTheBits.py.  That said, the challenge will be simply to understand how they all work so you can pull the various pieces together as needed.