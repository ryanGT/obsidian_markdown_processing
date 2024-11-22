from krauss_misc import rwkos, txt_mixin
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



class obsidian_markdown_processor(txt_mixin.txt_file_with_list):
    """The main idea is that this processor will find a markdown
    file in an Obsidian vault and then operate on that file in 
    some way, most likely leading to generating a pdf document."""
    def __init__(self, obs_root):
        self.obs_root = obs_root


    def find_markdown_file(self, mypat):
        matches = rwkos.glob_all_subdirs(self.obs_root,mypat)
        assert len(matches) > 0, "Did not find a match for %s in %s" % \
                (mypat, self.obs_root)
        assert len(matches) == 1, "Found more than one match for %s:\n %s" % \
                (mypat, matches)
        return matches[0]




class obsidian_345_slides_procesor(obsidian_markdown_processor):
    """The main use case for me for Obsidian stuff is that I need
    to generate lecture slides based on pandoc and latex beamer.

    So, this class will help find the slides for a current lecture 
    number based on the assumption that there is exactly one file
    matching 'Class %i -*.md' somewhere underneath a class prep root
    folder.  Note that the C in Class is capital and whatever follows
    the hyphen is the lecture title.

    The primary role of this class is to get the Obsidian markdown 
    file copied into the correct class prep folder (one folder per 
    class period) and prepared for pandoc to convert the markdown to 
    latex.  One key is converting the Obsidian ![[filename]] image syntax
    to various flavors of \myfig{width}{path}.  It is assumed that
    there will be exactly one match for filename underneath an Obsidian
    images root."""
    def __init__(self, classnum, obs_class_prep_root, obs_images_root=None):
        obsidian_markdown_processor.__init__(self, obs_class_prep_root)
        self.classnum = classnum
        self.obs_class_prep_root = obs_class_prep_root
        if obs_images_root is None:
            obs_images_root = obs_class_prep_root
        self.obs_images_root = obs_images_root


    def find_markdown_file(self):
        mypat = "Class %i -*.md" % self.classnum
        return obsidian_markdown_processor.find_markdown_file(self, mypat)
        

