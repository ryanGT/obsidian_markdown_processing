from krauss_misc import rwkos
import os, shutil, re, glob


def find_next_folder_num(myroot=".", pat="class_%0.2i_*"):
    """I typically create a class folder for each lecture period.  They are
    numbered with zero padding.  I want to find the next one that needs to be
    created.

    Go to myroot and search for pat % i until it fails.  The i that fails is
    the next folder to create."""
    os.chdir(myroot)

    for i in range(1,200):
        mypat = pat % i
        if "*" not in mypat:
            print("note: no * in pat: %s" % pat)
        matches = glob.glob(mypat)
        if len(matches) == 0:
            return i

