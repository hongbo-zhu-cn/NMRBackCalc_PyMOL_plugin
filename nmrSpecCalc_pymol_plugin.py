""" 2014_02_08: Hongbo Zhu
    DESCRIPTION: Calculate NMR spectra for atoms within a sphere of 
        a selection. 
        All atoms are saved to PDB. The spectra of the 
        saved atoms are calculated.
"""

###################### USER PARAMETERS starts here #####################
# Do update the following parameters according to your setup before    #
# running the script:                                                  #

# bcalc_binary = '/home/hzhu/projects/nmrCalc/NMRspiritC++-1.1/NMRspiritC++'

#                                                                      #
#                                                                      #
###################### USER PARAMETERS ends here #######################



# python lib
import os, sys, time, copy, subprocess, shutil
#from collections import OrderedDict

import Tkinter
import tkSimpleDialog
import tkMessageBox
import tkFileDialog
import tkColorChooser


# pymol lib
try: 
    from pymol import cmd, stored
    from pymol.cgo import *
except ImportError:
    print 'Warning: pymol library cmd not found.'
    sys.exit(1)
    
# external lib    
try:
    import Pmw
except ImportError:
    print 'Warning: failed to import Pmw. Exit ...'
    sys.exit(1)

VERBOSE = True
three_to_one = {'CYS': 'C', 'ASP': 'D', 'SER': 'S', 'GLN': 'Q', 'LYS': 'K',
                'ILE': 'I', 'PRO': 'P', 'THR': 'T', 'PHE': 'F', 'ASN': 'N', 
                'GLY': 'G', 'HIS': 'H', 'LEU': 'L', 'ARG': 'R', 'TRP': 'W', 
                'ALA': 'A', 'VAL': 'V', 'GLU': 'E', 'TYR': 'Y', 'MET': 'M'}

#################
## here we go
#################
def __init__(self):
    """ MSMS plugin for PyMol
    """
    self.menuBar.addmenuitem('Plugin', 'command',
                             'NMRspiritC++', label = 'NMRspiritC++',
                             command = lambda s=self : NMRSpecCalc(s))
    

#################
## GUI related
#################
class NMRSpecCalc:
  
    def __init__(self, app):
        
        self.parent = app.root
        self.dialog = Pmw.Dialog(self.parent,
                                 buttons = ('Spectra Back-Calc', 'Exit'),
                                 title = 'NMRspiritC++ pluging for PyMOL',
                                 command = self.execute)
        Pmw.setbusycursorattributes(self.dialog.component('hull'))

        # parameters used by NMRSpecCalc
        self.center_sel       = Tkinter.StringVar()
        self.radius           = Tkinter.DoubleVar()
        self.radius.set(5.0)
        self.f3width          = Tkinter.DoubleVar()
        self.apply_f3width    = Tkinter.BooleanVar()
        self.f3left           = Tkinter.DoubleVar()
        self.apply_f3left     = Tkinter.BooleanVar()
#        self.assign           = Tkinter.BooleanVar()  # replaced by -thres
        self.thres            = Tkinter.IntVar()
        self.thres.set(5)
        self.apply_thres      = Tkinter.BooleanVar()
        self.apply_thres.set(True)
        self.vlong            = Tkinter.IntVar()
        self.apply_vlong      = Tkinter.BooleanVar()
        self.filter           = Tkinter.IntVar()
        self.apply_filter     = Tkinter.BooleanVar()
        self.bcalc_binary     = Tkinter.StringVar()
        self.user_bcalc_home  = Tkinter.StringVar()
        self.back_calc_home   = Tkinter.StringVar()
        
        if 'BACK_CALC_BINARY' in os.environ:
            if VERBOSE:
                print 'INFO: Found BACK_CALC_BINARY in environmental variables', \
                      os.environ['BACK_CALC_BINARY']
            self.bcalc_binary.set(os.environ['BACK_CALC_BINARY'])
        else:
            if VERBOSE: print 'INFO: BACK_CALC_BINARY not found in environmental variables.'

        if 'USER_BCALC_HOME' in os.environ:
            if VERBOSE:
                print 'INFO: Found USER_BCALC_HOME in environmental variables', \
                      os.environ['USER_BCALC_HOME']
            self.user_bcalc_home.set(os.environ['USER_BCALC_HOME'])
        else:
            if VERBOSE: print 'INFO: USER_BCALC_HOME not found in environmental variables.'
           
        if 'BACK_CALC_HOME' in os.environ:
            if VERBOSE:
                print 'INFO: Found BACK_CALC_HOME in environmental variables', \
                      os.environ['BACK_CALC_HOME']
            self.back_calc_home.set(os.environ['BACK_CALC_HOME'])
        else:
            if VERBOSE: print 'INFO: BACK_CALC_HOME not found in environmental variables.'

            
        w = Tkinter.Label(self.dialog.interior(),
                          text = '\nNMRSpecCalc Plugin for PyMOL\nHongbo Zhu, 2014.\n\nNMR Spectra Back Calculation Plugin.',
                          background = 'black',
                          foreground = 'green'
                          )
        w.pack(expand = 1, fill='both', padx=10, pady=5)

        # make a few tabs within the dialog
        self.notebook = Pmw.NoteBook(self.dialog.interior())
        self.notebook.pack(fill = 'both', expand=1, padx=10, pady=10)

        ######################
        # Tab : NMRSpecCalc Tab
        ######################
        page = self.notebook.add('NMRSpecCalc')       
        self.notebook.tab('NMRSpecCalc').focus_set()

        group_selsphere = Tkinter.LabelFrame(page, text='Selection Sphere')
        group_selsphere.grid(sticky='eswn', row=0, column=0, 
                             columnspan=2, padx=10, pady=3)
        group_loc = Tkinter.LabelFrame(page, text = 'Locations')
        group_loc.grid(sticky='eswn',row=1,column=0, columnspan=2, padx=10, pady=3)
        group_param = Tkinter.LabelFrame(page, text = 'Parameters')
        group_param.grid(sticky='eswn',row=0, column=2, 
                         rowspan=2, columnspan=2, padx=10, pady=3)
        page.columnconfigure(0, weight=2)
        page.columnconfigure(1, weight=1)
                
        center_sel_ent = Pmw.EntryField(group_selsphere,
                                        label_text='Center selection:',
                                        labelpos='wn',
                                        entry_textvariable=self.center_sel
                                        )
        radius_ent = Pmw.EntryField(group_selsphere, 
                                    labelpos = 'wn',
                                    label_text='radius:',
                                    value=self.radius.get(),
                                    validate = {'validator':'real', 'min':0},
                                    entry_textvariable=self.radius,
                                    entry_width=10
                                    )
        # arrange widgets using grid
        center_sel_ent.grid(sticky='we', row=0, column=0, padx=5, pady=2)
        radius_ent.grid(sticky='we', row=0, column=1, padx=5, pady=2)
        
        
        bcalcbin_ent = Pmw.EntryField(group_loc,
                                      label_text = 'NMRspiritC++_bin:', labelpos='wn',
                                      entry_textvariable=self.bcalc_binary)
        bcalcbin_but = Tkinter.Button(group_loc, text = 'Browse...',
                                       command = self.getBCalcBinary)
        ubcalhome_ent = Pmw.EntryField(group_loc,
                                       label_text = 'USER_BCALC_HOME:', labelpos='wn',
                                       entry_textvariable=self.user_bcalc_home)
        ubcalhome_but = Tkinter.Button(group_loc, text = 'Browse...',
                                       command = self.getUserBCalcHome)
        bcalhome_ent = Pmw.EntryField(group_loc,
                                      label_text = 'BACK_CALC_HOME:', labelpos='wn',
                                      entry_textvariable=self.back_calc_home)
        bcalhome_but = Tkinter.Button(group_loc, text = 'Browse...',
                                      command = self.getBackCalcHome)
        
        # arrange widgets using grid
        bcalcbin_ent.grid(sticky='we', row=0, column=0, padx=5, pady=1)
        bcalcbin_but.grid(sticky='we', row=0, column=1, padx=5, pady=1)
        ubcalhome_ent.grid(sticky='we', row=1, column=0, padx=5, pady=1)
        ubcalhome_but.grid(sticky='we', row=1, column=1, padx=5, pady=1)
        bcalhome_ent.grid(sticky='we', row=2, column=0, padx=5, pady=1)
        bcalhome_but.grid(sticky='we', row=2, column=1, padx=5, pady=1)
        group_loc.columnconfigure(0, weight=9)
        group_loc.columnconfigure(1, weight=1)

        f3width_ent = Pmw.EntryField(group_param, 
                                     labelpos = 'wn',
                                     label_text='f3width:',
                                     value=self.f3width.get(),
                                     validate = {'validator':'real', 'min':0},
                                     entry_textvariable=self.f3width,
                                     entry_width=10,
                                     entry_state=self.apply_f3width.get() and 'normal' or 'disabled'
                                     )
        f3left_ent = Pmw.EntryField(group_param, labelpos = 'wn',
                                    label_text='f3left:',
                                    value=self.f3left.get(),
                                    validate = {'validator':'real', 'min':0},
                                    entry_textvariable=self.f3left,
                                    entry_width=10,
                                     entry_state=self.apply_f3left.get() and 'normal' or 'disabled'
                                    )
        thres_ent = Pmw.EntryField(group_param, labelpos = 'wn',
                                   label_text='thres:',
                                   value=self.thres.get(),
                                   validate = {'validator':'integer', 'min':0},
                                   entry_textvariable=self.thres,
                                   entry_width=10,
                                   entry_state=self.apply_thres.get() and 'normal' or 'disabled'
                                )
        vlong_ent = Pmw.EntryField(group_param, labelpos = 'wn',
                                   label_text = 'vlong:', 
                                   value=self.vlong.get(),
                                   validate = {'validator':'integer', 'min':0},
                                   entry_textvariable=self.vlong,
                                   entry_width=10,
                                   entry_state=self.apply_vlong.get() and 'normal' or 'disabled'
                                   )
        filter_ent = Pmw.EntryField(group_param, labelpos = 'wn',
                                    label_text = 'filter:', 
                                    value=self.vlong.get(),
                                    validate = {'validator':'integer', 'min':0},
                                    entry_textvariable=self.filter,
                                    entry_width=10,
                                    entry_state=self.apply_filter.get() and 'normal' or 'disabled'
                                    )
#        assign_cb = Tkinter.Checkbutton(group_param,
#                                        text='-assign.', 
#                                        variable=self.assign,
#                                        onvalue=True, offvalue=False,
#                                        command=lambda e=thres_ent, v=self.assign: \
#                                            self.entryCheck(e,v))
        f3width_cb = Tkinter.Checkbutton(group_param,
                                         text='',
                                         variable=self.apply_f3width,
                                         onvalue=True, offvalue=False,
                                         command=lambda e=f3width_ent, v=self.apply_f3width: \
                                             self.entryCheck(e,v))
        f3left_cb = Tkinter.Checkbutton(group_param,
                                        text='',
                                        variable=self.apply_f3left,
                                        onvalue=True, offvalue=False,
                                        command=lambda e=f3left_ent,v=self.apply_f3left: \
                                            self.entryCheck(e,v))
        thres_cb = Tkinter.Checkbutton(group_param,
                                       text='',
                                       variable=self.apply_thres,
                                       onvalue=True, offvalue=False,
                                       command=lambda e=thres_ent, v=self.apply_thres: \
                                           self.entryCheck(e,v))
        vlong_cb = Tkinter.Checkbutton(group_param,
                                       text='',
                                       variable=self.apply_vlong,
                                       onvalue=True, offvalue=False,
                                       command=lambda e=vlong_ent, v=self.apply_vlong: \
                                           self.entryCheck(e,v))
        filter_cb = Tkinter.Checkbutton(group_param,
                                        text='',
                                        variable=self.apply_filter,
                                        onvalue=True, offvalue=False,
                                        command=lambda e=filter_ent, v=self.apply_filter: \
                                            self.entryCheck(e,v))

        f3width_ent.grid(sticky='we', row=1, column=0, padx=5, pady=3)
        f3width_cb.grid(sticky='e', row=1, column=1, padx=0, pady=3)

        f3left_ent.grid(sticky='we', row=2, column=0, padx=5, pady=3)
        f3left_cb.grid(sticky='e', row=2, column=1, padx=0, pady=3)

        thres_ent.grid(sticky='we', row=3, column=0, padx=5, pady=3)
        thres_cb.grid(sticky='e', row=3, column=1, padx=0, pady=3)

        vlong_ent.grid(sticky='we', row=4, column=0, padx=5, pady=3)
        vlong_cb.grid(sticky='e', row=4, column=1, padx=0, pady=3)

        filter_ent.grid(sticky='we', row=5, column=0, padx=5, pady=3)
        filter_cb.grid(sticky='e', row=5, column=1, padx=0, pady=3)

        group_param.columnconfigure(0, weight=5)
        group_param.columnconfigure(1, weight=1)


        ######################
        # Tab : About Tab
        ######################
        page = self.notebook.add('About')
        group_about = Pmw.Group(page, tag_text = 'About')
        group_about.pack(fill = 'both', expand = 1, padx = 10, pady = 5)

        self.notebook.setnaturalsize()    

        return


    def getBCalcBinary(self):
        bcalc_bin = tkFileDialog.askopenfilename(
            title='Please select NMRspiritC++ binary', initialdir='',
            filetypes=[('all','*')], parent=self.parent)
        if  bcalc_bin:
            self.bcalc_binary.set(bcalc_bin)
        return


    def getUserBCalcHome(self):
        user_bcalc_home = tkFileDialog.askdirectory(
            title='Please select USER_BCALC_HOME directory', initialdir='',
            parent=self.parent, mustexist=True)
        if user_bcalc_home:
            self.user_bcalc_home.set(user_bcalc_home)
        return


    def getBackCalcHome(self):
        back_calc_home = tkFileDialog.askdirectory(
            title='Please select BACK_CALC_HOME directory', initialdir='',
            parent=self.parent, mustexist=True)
        if back_calc_home:
            self.back_calc_home.set(back_calc_home)
        return


    def entryCheck(self, e, v):
        if v.get() == True:
            e.configure(entry_state='normal') # EntryFiled uses entry_state
        else:
            e.configure(entry_state='disabled')
        return


    def execute(self, cmd):
        if cmd == 'Spectra Back-Calc':
            user_center_sel = self.center_sel.get()
            print 'INFO: Center selection:', user_center_sel
            if len(user_center_sel) > 0:
                nmrSpecCalcSphere(center=user_center_sel,
                                  radius=self.radius.get(),
                                  bcalc_binary=self.bcalc_binary.get(),
                                  project_home=self.user_bcalc_home.get(),
                                  backcalc_home=self.back_calc_home.get(),
                                  f3width=self.apply_f3width.get() and self.f3width.get() or None,
                                  f3left=self.apply_f3left.get() and self.f3left.get() or None,
                                  thres=self.apply_thres.get() and self.thres.get() or None,
                                  vlong=self.apply_vlong.get() and self.vlong.get() or None,
                                  filterres=self.apply_filter.get() and self.filter.get() or None
                                  )
        elif cmd == 'Exit':
            print 'Exiting NMRSpecCalc Plugin ...'
            if __name__ == '__main__':
                self.parent.destroy()
            else:
                self.dialog.withdraw()
            print 'Done.'
        else:
            print 'Exiting NMRSpecCalc Plugin ...'
            self.dialog.withdraw()
            print 'Done.'

        return

    
    def quit(self):
        self.dialog.destroy() 



## ------------------ here comes the code irrelevant to GUI ---------------


def renameHN(pdb_fn):
    """ Rename protons to H if their names are any of ['HN','HT1','HT2','HT3']
    """
    newfd = []
    for line in open(pdb_fn).readlines():
        if line.startswith('ATOM  ') and line[12:16] in [' HN ',' HT1',' HT2',' HT3']:
            newline = line[:12] + ' H  ' + line[16:]
            newfd.append(newline)
        else:
            newfd.append(line)
    open(pdb_fn, 'w').writelines(newfd)

    return


def readChemshifts(cs_fn):
    """ Read chemshifts file and put it in a dict, where keys are the 
        first 17 characters in the line and values are the line.
    """
    cs_dict = dict([(line[:17], line) for line in open(cs_fn).readlines()])
    return cs_dict


def readAverageShift(ss_fn):
    """ Read average shift value from the chemical shift statistics table

    """
    avgshift = {}
    for line in open(ss_fn).readlines():
        buf = line.split()
        if len(buf) > 0 and buf[0] in three_to_one.values():
            avgshift['%s:%s' % (buf[0], buf[1])] = buf[6]

    return avgshift


def readSimuParam(sp_fn):
    """ Read simulation parameter file and put the value in a dictionary.
        Key is parameter_name, value is list of parameter values
    """
    sp_dict = {}
    sp_list = []
    for line in open(sp_fn).readlines():
        if len(line.strip()) > 0 and line.startswith('#'):
            buf = line.rstrip().split()
            if len(buf) > 1:
                sp_dict[buf[0][1:-1]] = buf[1:]
                sp_list.append(buf[0][1:-1])

    return sp_dict, sp_list 


def writeSimuParam(sp_dict, sp_list, sp_fn):
    """ Write simulation parameters into file. 
        Note the parameters are stored in a dictionary. sp_list is to
        preserve the order of param as the original file.
        OrderedDict is not used here in case the user has an old version of python.
    """
    open(sp_fn, 'w').writelines(
        ['#%s: %s\n' % (k, ' '.join(sp_dict[k])) for k in sp_list])

    return


def generateSeq(sel, obj, chn):
    """ Generate a sequence for back-calc.
        If a residue in the protein is selected for back-calc, it is 
        included in the seq. Otherwise an X is put at the position.
    """
    # get the sequence of the parent object & chain
    stored.list = []
    if chn == " ":
        cmd.iterate("\"%s\" and n. ca" % (obj,), 
                    "stored.list.append((resi,resn))")
    else:
        cmd.iterate("\"%s\" and chain \"%s\" and n. ca" % (obj, chn), 
                    "stored.list.append((resi,resn))")
    reslist = stored.list

    # get the sequence of the residues in the selection sphere
    stored.list = []
    cmd.iterate(sel + " and n. CA", "stored.list.append((resi,resn))")
    sel_res_dict = dict(zip(stored.list, range(len(stored.list))))

    seq = []
    for r in reslist:
        if r in sel_res_dict: 
            seq.append(three_to_one[r[1]])
        else:
            seq.append('X')
    seq_str = ''.join(seq)

    return seq_str


def defineShiftRange(displayed, cs_fn, f3width, f3left):
    """ Define shift range of selected atoms
        @param displayed: hydrogen atoms in the center selection or covalently
          bonded to any atoms in the center selection
    """

    # define shift range of selected atoms
    maxf3, minf3 = -10000.0, 10000.0
    # get the chemshifts of the atoms in the selection sphere
    # make a copy of the chemshifts file first
    shutil.copyfile(cs_fn, cs_fn+'.bak')
    cs_dict = readChemshifts(cs_fn)
    cs_list = []
    stored.list = []
    cmd.iterate(displayed, "stored.list.append((resi,resn,name))")
    for resi,resn,name in stored.list:
        if name in ['HN','HT1','HT2','HT3']: name = 'H'  # rename proton collecting to bb N
        k = "%5s   %s  %4s" % (resi, resn, name)
        try:
            cs_list.append(cs_dict[k])
            csv = float(cs_dict[k][18:26])
            if csv > maxf3: maxf3 = csv
            if csv < minf3: minf3 = csv
        except KeyError:
            #pass # TODO: check the output.txt after back-calc
             print "INFO: Could not find chemshift for", k
    #for cs in cs_list: print cs # debug print

    f3shift = maxf3 + 0.2                      # left edge of the spectrum
    f3sweep = maxf3 - minf3 + 0.4              # direct 1H sweep width
    if f3width is not None: f3sweep = f3width  
    if f3left  is not None: f3shift = f3left

    return f3sweep, f3shift


def backCalculation(sp, bcalc_binary, proj_home, f3sweep, f3shift):
    """ Back calculation 
    """

    print "INFO: Back-calculating %s spectrum ..." % (sp,)
    sp_dir = '%s/%s' % (proj_home, sp)
    if not os.path.isdir(sp_dir):
        print "WARNING: Parameters for the %s spectrum are not defined; skipping..." % (sp,)

    # read in simulation parameters and make specific changes
    par_fn = '%s/%s/simulationparameters' % (proj_home, sp)
    shutil.copyfile(par_fn, par_fn+'.bcalc.bak')
    param_dict, param_list = readSimuParam(par_fn)
    param_dict['rfpm'][2] = str(10)         # an arbitrary f1 shift for all atoms - the real 
                                            # shift is irrelevant for a 2D slice
    param_dict['rfpm'][0] = str(f3shift)    # left edge of the spectrum in f3
    param_dict['spwd'][0] = str(f3sweep * float(param_dict['freq'][0]))  # sweep width in f3 (Hz)

    sizef3 = 32
    while (sizef3 <= int(f3sweep * float(param_dict['freq'][0])/16.0)):
        sizef3 *= 2
    param_dict['size'][0] = str(sizef3)
    writeSimuParam(param_dict, param_list, par_fn)

    old_dir = os.getcwd()
    os.chdir(sp_dir)
    proc = subprocess.Popen([bcalc_binary, par_fn],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                            )
    bcalc_stdout, bcalc_stderr = proc.communicate()
    print "INFO: ---- Back calculation output ----"
    print bcalc_stdout
    if bcalc_stderr is not None: 
        print "ERROR: ---- Back calculation error: ----"
        print bcalc_stderr

    os.chdir(old_dir)
    return


def postProcess(sp, displayed_sel, proj_home, bcalc_home, thres, vlong, flter):

    sp_dir = '%s/%s' % (proj_home, sp)
    old_dir = os.getcwd()
    os.chdir(sp_dir)

    # Post-processing spectra
    print "\nINFO: ---- Post processing ... ----"
    postpro_pl = '%s/post-process.pl' % (bcalc_home,)
    stored.list = []
    cmd.iterate(displayed_sel, "stored.list.append((resi,name))")
    # all protons in displayed must be from the same residue

    for r,h in stored.list: assert r == stored.list[0][0]

    protonlist = []
    for r,n in stored.list:
        if n in ['HN','HT1','HT2','HT3']:
            protonlist.append('H')
        else:
            protonlist.append(n)
    displayed = '%s:%s' % (stored.list[0][0], ':'.join(protonlist))
#    cmdline = [postpro_pl, sp, displayed, '-assign']
    cmdline = [postpro_pl, sp, displayed]
    if thres is not None: 
        cmdline.append('-thres')
        cmdline.append(str(thres))
    if vlong is not None: 
        cmdline.append('-vlong') 
        cmdline.append(str(vlong))
    if flter is not None: 
        cmdline.append('-filter')
        cmdline.append(str(flter))
    print 'DEBUG: command line', cmdline        
#    proc = subprocess.Popen(cmdline,
#                            stdout=subprocess.PIPE,
#                            stderr=subprocess.STDOUT
#                            )
#    pproc_stdout, pproc_stderr = proc.communicate()
#    print "INFO: ---- Post-processing output ----"
#    print pproc_stdout
#    if pproc_stderr is not None: 
#        print "ERROR: ---- Post-processing error: ----"
#        print pproc_stderr

    os.chdir(old_dir)
    return


def nmrSpecCalcSphere(center, radius, **kwargs):
    """ Interface to sphere selection.

        @param center: the center of the selection shell (spherical).
          Center is a PyMOL selection. It may contain protons or heavy atoms.
          The residues of the atoms are the real center for selection shell!

        @param radius: radius of the selection sphere
    """
    radius = float(radius)

    # get the parent objects
    olist = cmd.get_object_list(center)
    if len(olist) == 0:
        print "ERROR: No objects in center selection:", center
        return
    elif len(olist) > 1:
        print "WARNING: There are multiple objects in the center selection:"
        for o in olist: print o
        print "         Only the 1st object is considered:", olist[0]

    obj = olist[0]

    # get the parent chains
    clist = cmd.get_chains(center)
    if len(clist) == 0: 
        print "INFO: No chain names detected in center selection:", center
        print "      Consider chain name empty."
        clist = [" "]
    elif len(clist) > 1:
        print "WARNING: There are multiple chains in the center selection:"
        for c in clist: print c
        print "         Only the 1st chain is considered:", clist[0]

    chn = clist[0]

    # get parent residues
    # all residues involved in center are taken as center for
    # selection sphere
    stored.list = []
    cmd.iterate(center, 'stored.list.append(resi)' ) # do not use the n. CA trick because there may be no CA in the center selection
    unik_resi = []
    for i in stored.list:
        if i not in unik_resi: unik_resi.append(i)
    center_res = "%s//\"%s\"/%s/" % (obj, chn.strip(), '+'.join(unik_resi))

    # save selection to temp pdb output
    if chn == " ":
        sel = "%s and (byres %s expand %d)" % \
            (obj, center_res, radius)
    else:
        sel = "%s and chain \"%s\" and (byres %s expand %d)" % \
            (obj, chn, center_res, radius)

    # get selected N/C atoms (for deciding which spactra to calc)
    stored.list = []
    cmd.iterate(center, 'stored.list.append(name)')
    NC_atoms = [n for n in stored.list if n[0] in ['C', 'N']]
    if not NC_atoms:  # if no N/C atoms found, expand to connected atoms
        print 'INFO: No N/C atoms found in center selection.'
        print 'INFO: Try to examine atoms covalently bonded to center selection.'
        conn_heavy_atoms = '(' + center + ' around 1.2) and (not hydro)' # use around to exclude center
        stored.list = []
        cmd.iterate(conn_heavy_atoms, 'stored.list.append(name)')
        NC_atoms = [n for n in stored.list if n[0] in ['C', 'N']]

    # find out which spectra to calc (only if parameter 'spectra' is not specified)
    has_N, has_C = False, False
    print 'INFO: N/C atoms in the center selection or atoms covalently bonded:', ','.join(NC_atoms)
    for a in NC_atoms:
        if a[0] == 'N': has_N = True
        elif a[0] == 'C': has_C = True

    spectra_to_calc = []

    if has_N and has_C:
        spectra_to_calc = ['HNH','CNH','NNH','HCH','CCH']
    elif has_N:
        spectra_to_calc = ['HNH','CNH','NNH']
    elif has_C:
        spectra_to_calc = ['HCH','CCH']
    else:
        print 'WARNING: No N/C atoms found in center selection or atoms covalently bonded.'
        print 'WARNING: All spectra (HNH,CNH,NNH,HCH,CCH) will be tried.'
        spectra_to_calc = ['HNH','CNH','NNH','HCH','CCH']

    if 'spectra' not in kwargs:
        kwargs['spectra'] = spectra_to_calc
        print 'INFO: Spectra to calc:', ','.join(spectra_to_calc)
    else:
        print 'INFO: Spectra to calc (as user specified):', ','.join(kwargs['spectra'])

    # get protons in center
    # if there are any heavy atoms in center, the proton connected are included
    # use distance cutoff to find hydrogens within distance of 1.2
    # PyMOL itself uses distance as criterion to detect covalent bonds
    center_hydro = '(' + center + ' expand 1.2) and hydro'  # use expand to include center
    stored.list = []
    cmd.iterate(center_hydro, 'stored.list.append((resi, resn, name))')
    print "INFO: hydrogen atoms in the center:"
    for h in stored.list: print '     ',h

    try:
        del kwargs['_self'] # from PyMOL
    except KeyError:
        pass
    _nmrSpecCalc(sel=sel, obj=obj, chn=chn, cth=center_hydro, **kwargs)

    return


def _nmrSpecCalc(sel, obj, chn, cth,
                 #spectra=['HNH'],
                 bcalc_binary, project_home, backcalc_home,
                 spectra=['HNH','CNH','NNH','HCH','CCH'], 
                 f3width=None, f3left = None,
                 thres=None, vlong=None, filterres=None,
                 verbose=True):
    """
        @param sel: all selected atoms within the selection sphere
        @param obj: the parent object of the defined center of selection sphere
        @param chn: the parent chain of the defined center of selection sphere
        @param cth: all hydrogens within the center selection of covalently
          bonded to any atoms in the center selection
    """
    ## try:
    ##     project_home  = os.environ['USER_BCALC_HOME']
    ##     backcalc_home = os.environ['BACK_CALC_HOME']
    ## except KeyError:
    ##     print "ERROR: Please setup environmental variable USER_BCALC_HOME and BACK_CALC_HOME."
    ##     print "       Quit ..."
    ##     return

    pdb_fn = '%s/model/model.pdb'     % (project_home,)
    seq_fn = '%s/model/modelsequence' % (project_home,)
    mcs_fn = '%s/model/modelshifts'   % (project_home,)
    sst_fn = '%s/perl/data/chem_shift_statistics.tab' % (backcalc_home,)

    # save selected atoms to a pdb file
    cmd.set(name='pdb_use_ter_records', value=0) # surpress insertion of TER when seq is non-continuous
    cmd.save(pdb_fn, sel)
    renameHN(pdb_fn)  # rename atom names ['HN','HT1','HT2','HT3'] to H

    if verbose: 
        print "INFO: Selection %s saved to file %s" % (sel, pdb_fn)

    # save seq for back-calc
    seq = generateSeq(sel, obj, chn)
    open(seq_fn, 'w').writelines(seq+'\n')
    if verbose: 
        print "INFO: Sequence %s saved to file %s" % (seq, seq_fn)

    # copy chemshifts file
    avgshift_dict = readAverageShift(sst_fn)
    cs_fn = '%s/data/chemshifts' % (project_home,)
    newcs = []
    for line in open(cs_fn).readlines():
        if len(line) > 25 and line[18:26] == '-999.900':
            k = "%s:%s" % (three_to_one[line[8:11]], line[13:17].strip())
            acs = avgshift_dict[k]
            newcs.append('%s%7s0\n' % (line[:18], acs))
        else:
            newcs.append(line[:26]+'\n')
    open(mcs_fn, 'w').writelines(newcs)
    if verbose: 
        print "INFO: Modelshifts saved to file %s" % (mcs_fn,)

    # define shift range
    f3sweep, f3shift = defineShiftRange(cth, cs_fn, f3width, f3left)

    # actual back-calculation + post-processing
    if thres is not None: thres = int(thres)  # parameters for post-processing
    if vlong is not None: vlong = int(vlong)
    if filterres is not None: filterres = int(filterres)

    print 'INFO: Spectra to calc:', ','.join(spectra)
    for sp in spectra:
        backCalculation(sp, bcalc_binary, project_home, f3sweep, f3shift)
        postProcess(sp, cth, project_home, backcalc_home, thres, vlong, filterres)
    # search output.txt for missing shifts
    print "INFO: Back calculation and post-processing finished."

    return


# also works by command line
cmd.extend('nmrSpecCalcSphere', nmrSpecCalcSphere)


#############################################
#
#
# Create demo in root window for testing.
#
#
##############################################
if __name__ == '__main__':
    
    class App:
        def my_show(self,*args,**kwargs):
            pass

    app = App()
    app.root = Tkinter.Tk()
    Pmw.initialise(app.root)   
    app.root.title('What\'s up, Dude!')

    widget = NMRSpecCalc(app)
    app.root.mainloop()
