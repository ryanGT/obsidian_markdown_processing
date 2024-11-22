from krauss_misc import rwkos, txt_mixin
import os, shutil, re, glob, copy


obs_fig_p = re.compile(r"!\[\[(.*)\]\]")


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
    def __init__(self, obs_root, dst_dir=None, img_root=None):
        self.obs_root = obs_root
        self.dst_dir = dst_dir
        if img_root is None:
            img_root = obs_root
        self.img_root = img_root



    def find_markdown_file(self, mypat):
        matches = rwkos.glob_all_subdirs(self.obs_root,mypat)
        assert len(matches) > 0, "Did not find a match for %s in %s" % \
                (mypat, self.obs_root)
        assert len(matches) == 1, "Found more than one match for %s:\n %s" % \
                (mypat, matches)
        self.md_path_in = matches[0]
        return matches[0]


    def load_obsidian_md(self):
        self.txt_file = txt_mixin.txt_file_with_list(self.md_path_in)
        self.list = copy.copy(self.txt_file.list)


    def get_fig_inds(self):
        self.fig_inds = self.list.findall("![[",forcestart=1)


    def find_one_fig(self, obs_fig_name):
        # look for exactly one match below self.img_root
        matches = rwkos.glob_all_subdirs(self.img_root, obs_fig_name)
        assert len(matches) > 0, "Did not find a match for %s" % obs_fig_name
        assert len(matches) == 1, "Found more than one match for %s" % \
                    obs_fig_name
        return matches[0]



    def copy_one_fig(self, obs_fig_name, figfolder, \
                     prefer_pdf=True):
        full_fig_path = self.find_one_fig(obs_fig_name)

        # does a pdf exist?
        pne, ext = os.path.splitext(full_fig_path)
        if ext != '.pdf':
            pdf_test_path = pne + '.pdf'
            if os.path.exists(pdf_test_path) and prefer_pdf:
                full_fig_path = pdf_test_path
        rest, fn = os.path.split(full_fig_path)
        dst = os.path.join(figfolder, fn)
        shutil.copyfile(full_fig_path, dst)


    def get_fig_obs_paths(self):
        if not hasattr(self, "fig_inds"):
            self.get_fig_inds()

        fig_obs_paths = []

        for i in self.fig_inds:
            curline = self.list[i]
            q = obs_fig_p.search(curline)
            mypath = q.group(1)
            fig_obs_paths.append(mypath)

        self.fig_obs_paths = fig_obs_paths
        return self.fig_obs_paths


    def copy_images(self, figfolder=None):
        if figfolder is None:
            assert self.dst_dir is not None, \
                    "not sure where to put figures, dst_dir is None"
            figfolder = os.path.join(self.dst_dir, 'figs')
            rwkos.make_dir(figfolder)

        self.get_fig_inds()
        self.get_fig_obs_paths()
        
        for figpath in self.fig_obs_paths:
            self.copy_one_fig(figpath, figfolder)



    def save(self, outpath):
        txt_mixin.dump(outpath, self.list)



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
    def __init__(self, classnum, obs_class_prep_root, 
                 dst_dir=None, obs_images_root=None):
        obsidian_markdown_processor.__init__(self, obs_class_prep_root, \
                dst_dir=dst_dir, img_root=obs_images_root)
        self.classnum = classnum
        self.obs_class_prep_root = obs_class_prep_root
        if obs_images_root is None:
            obs_images_root = obs_class_prep_root
        self.obs_images_root = obs_images_root


    def find_markdown_file(self):
        mypat = "Class %i -*.md" % self.classnum
        return obsidian_markdown_processor.find_markdown_file(self, mypat)



    def guess_output_name(self):
        full_dst_path = os.path.abspath(self.dst_dir)
        print("full_dst_path = %s" % full_dst_path)
        rest, dst_folder_name = os.path.split(full_dst_path)
        print("dst_folder_name = %s" % dst_folder_name)
        assert dst_folder_name
        outname = dst_folder_name + '_slides.md'
        return outname



    def save(self, outpath=None):
        if outpath is None:
            outpath = self.guess_output_name()
        obsidian_markdown_processor.save(self, outpath)
        

