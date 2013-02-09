
from elementtree import ElementTree as ET
import os, gzip, tarfile, shutil, uuid
import config
from batch import Batch
from parse import Parse

class Process(object):

    def __init__(self, filename):
        self.filename = filename
        self.procid = uuid.uuid4().hex
        self.workdir = config.workdir + self.procid + '/'
        if not os.path.exists(config.workdir):
            try:
                os.makedirs(config.workdir)
            except:
                pass
        if not os.path.exists(self.workdir): os.makedirs(self.workdir)
        
    def process(self):
        print str(self.procid) + " processing " + self.filename
        if config.sourcetype == "pmcoa":
            self._process_pmcoa()
        elif config.sourcetype == "nlm":
            self._process_nlm()
        shutil.rmtree(self.workdir) # delete the folder in the workdir that was used for this process


    # process the pmcoa files as they come downloaded from pmcoa
    def _process_pmcoa(self):
        self._unpack_pmcoa() # results in folders in the workdir full of xml files to work on
        pmcoaList = os.listdir(self.workdir) # list the folders in the workdir
        b = Batch()
        p = Parse()
        for fl in pmcoaList:
            files = os.listdir(self.workdir + fl)
            for f in files:
                # these may still contain files. If so, need to go down one more level
                if os.path.isdir(self.workdir + fl + '/' + f):
                    fcs = os.listdir(self.workdir + fl + '/' + f)
                    for fr in fcs:
                        elem = self._ingest(self.workdir + fl + '/' + f + '/' + fr) # read the xml file
                        doc = p.parse(elem)
                        b.add( doc )
                else:
                    elem = self._ingest(self.workdir + fl + '/' + f) # read the xml file
                    doc = p.parse(elem)
                    b.add( doc )
        b.clear()
        del b


    # unpack a pmcoa file
    # pmcoa comes as ~4 files, each should be decompressed then untarred,
    # leaving folders full of xml files in the workdir
    def _unpack_pmcoa(self):
        tar = tarfile.open(config.filedir + self.filename)
        tar.extractall(path=self.workdir)
        tar.close()
        del tar


    # process the nlm files as they come downloaded from nlm
    def _process_nlm(self):
        self._unpack_nlm() # unpack the file to work on
        elements = self._ingest(self.workdir + self.filename) # read the xml file
        b = Batch()
        p = Parse()
        for sub in elements:
            doc = p.parse(sub)
            b.add( doc )
        b.clear()
        del b

    # unpack an nlm file
    # nlm comes as ~684 files, each one should be decompressed on disk
    def _unpack_nlm(self):
        tarobj = gzip.open(config.filedir + self.filename)
        outfile = open(self.workdir + self.filename, 'w')
        outfile.write(tarobj.read())
        outfile.close()
        del tarobj
            

    # read in then delete the xml file
    # this causes delay and requires enough free memory to fit the file
    def _ingest(self, filepath):
        tree = ET.parse(filepath)
        elements = tree.getroot()
        return elements



