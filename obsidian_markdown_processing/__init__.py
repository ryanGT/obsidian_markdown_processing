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


class obs_figure_syntax_processor(object):
    """A class to convert a chunk of lines from an obsidian markdown
    file that contain figure infomation into pandoc/latex code.

    The first line should contain ![[filename]].

    Subsequent lines could be blank or start with :fw:, :fh:, caption: 
    and label:"""
    def __init__(self, linesin, fig_folder_path, \
            default_width='0.9\\textwidth'):
        self.linesin = copy.copy(linesin)
        self.default_width = default_width
        self.fig_folder_path = fig_folder_path
        if fig_folder_path == 'figs':
            figfolder = fig_folder_path
        else:
            rest, figfolder = os.path.split(fig_folder_path)
        self.figfolder = figfolder



    def find_str(self, search_str):
        found = False
        for line in self.linesin:
            if search_str in line:
                found = True

        return found


    def find_line(self, search_str):
        """return the line containing search_str, if it is found
        in self.linesin"""
        for line in self.linesin:
            if search_str in line:
                return line


    def check_for_pdf(self):
        fno, ext = os.path.splitext(self.filename)
        if ext != '.pdf':
            pdf_name = fno + '.pdf'
            pdf_path = os.path.join(self.fig_folder_path, pdf_name)
            if os.path.exists(pdf_path):
                self.filename = pdf_name


    def parse(self):
        """Go through self.linesin and extract information:
           - filename
           - fw
           - fh
           - caption
           label"""
        q = obs_fig_p.search(self.linesin[0])
        self.filename = q.group(1)
        self.check_for_pdf()
        # how do I handle pdf files?
        # - if the pdf exists, use it
        # - does this processor have enough info to know 
        #   whether or not the pdf exists?
        attr_map = {':fw:':'fw', \
                    ':fh:':'fh', \
                    'caption:':'caption',\
                    'label:':'label'}
        for key, attr in attr_map.items():
            curline = self.find_line(key)
            if curline is not None:
                curline = curline.strip()
                if curline[0] == ':':
                    curline = curline[1:]
                rest, mystr = curline.split(':',1)
                mystr = mystr.strip()
                if "fw" in key:
                    val_str = mystr + '\\textwidth'
                elif "fh" in key:
                    val_str = mystr + '\\textheight'
                else:
                    val_str = mystr
            else:
                val_str = None

            setattr(self, attr, val_str)


    def convert_to_latex(self):
        # - do I have :fw: or :fh:?
        #     - that should affect my latex function
        # - do I have a caption or label?
        # - possible outputs:
        #     - \myfig{}{}
        #     - \myvfig{}{}
        #     - \mycapfig{}{}{}
        # - should one class try to handle all cases?
        self.parse()
        relpath = self.figfolder + '/' + self.filename 
        if self.caption is not None:
            if self.label is not None:
                self.caption += ' \\label{%s}' % self.label
            if self.fw is None:
                self.fw = self.default_width
            outline = "\\mycapfig{%s}{%s}{%s}" % \
                        (self.fw, relpath, self.caption)
        elif self.fh is not None:
            outline = "\\myvfig{%s}{%s}" % (self.fh, relpath)
        else:
            # defaut is myfig with default_width
            if self.fw is None:
                self.fw = self.default_width
            outline = "\\myfig{%s}{%s}" % (self.fw, relpath)

        N = len(self.linesin)
        linesout = ['']*N
        linesout[0] = outline
        self.linesout = linesout
        return linesout



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


    def get_fig_lines(self, ind, lines_to_check=5):
        """The figure lines start with the line that begins with
        ![[.  The figure lines may also include lines that start with 
        :fw:, :fh:, caption:, or label:, along with blank lines below 
        the first line

        The process will be to check a certain number of lines below
        the first line for lines that start with an optional string."""
        first_line = self.list[ind]

        opt_list = [":fw:", ":fh:", "caption:", "label:"]

        for i in range(1, lines_to_check+1):
            curline = self.list[ind + i]
            if curline.strip():
                # the line is not blank
                # - check to see if it contains any of the optional strings
                found_one = False
                for item in opt_list:
                    if item in curline:
                        found_one = True
                        break
                if not found_one:
                    # the line was not blank and it contains non-figure
                    # related content
                    # - so, we are done and the figure lines 
                    #   end at the previous line
                    end_ind = ind + i - 1

        # how do I want to handle blank lines at the end of the 
        # figure lines?
        # - backup to the last non-blank line
        for i in range(lines_to_check):
            curline = self.list[end_ind - i]
            if curline.strip():
                # the line is not blank
                end_ind -= i
                break
        return self.list[ind:end_ind+1]

    


    def  process_one_figure(self, ind, figfolder="figs"):
        """For each figure line that starts with ![[, convert that 
        line (and possibly subsequent lines) to \myfig{}{}, 
        \myvfig{}{} or \mycapfig{}{}

        check subsequent lines for :fw:, :fh:, and possibly caption:
        and label:

        How do I do this in a general way that subclasses can adapt?
        - is it sufficient that the presence of caption triggers
          myfigcap?

        :fh: and :fw: might be present in multiple output formats
        - I want to extact the information in a reusable way
        - each subclass would then decide what to do with the information

        - does a helper class make sense here?
        """
        fig_lines = self.get_fig_lines(ind)
        figdir1 = os.path.join(self.dst_dir, figfolder)
        figdir = os.path.abspath(figdir1)
        myprocessor = obs_figure_syntax_processor(fig_lines, \
                       fig_folder_path=figdir)
        myprocessor.parse()
        outlines = myprocessor.convert_to_latex()

        N = len(outlines)
        self.list[ind:ind+N] = outlines
 


    def process_figure_syntax(self):
        """Convert obsidian figure syntax to pandoc/latex by 
        calling process_one_figure for each figure line index."""
        if not hasattr(self, "fig_inds"):
            self.get_fig_inds()

        for i in self.fig_inds:
            self.process_one_figure(i)




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
        

