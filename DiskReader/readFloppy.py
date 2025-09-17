#----------------------------------------------#
# APPLEDOS utility                             #
#                                              #
# read .dsk file (144 K)                       #
#                                              #
#----------------------------------------------#

import argparse

#
# main class, contains the directory content and
# list aof associated file
#
class DSK:
  def __init__(self):
    self.filelist = {}
    self.nbfile = 0
  
  def read(self,fn):
    fi = open(fn,mode="rb")
    self.storage  = fi.read()
    fi.close()

  def sectOffset(self,track,sec):
    return (track*16+sec)*256
    
  def getByte(self,offset):
    return ord(self.storage[offset])
  #
  # add a file entry to the directory, a number is associated
  # to each file
  #  
  def addEntry(self,typ,trkT,secT,siz,name):
    self.filelist[self.nbfile] = CATENTRY(typ,trkT,secT,siz,name)
    self.nbfile+=1
  
  #
  # display directory content
  #  
  def dispDir(self):
    for n in range(self.nbfile):
       self.filelist[n].display()
  
  #
  # search a file with its dos name (28 char long)
  # return the file index if found -1 otherwise
  #    
  def findfile(self,na):        
    for n in range(self.nbfile):
      if (na==self.filelist[n].name):
        return n
    return -1
  
  #
  # builds up file content for all entries
  # in the directory
  # file content merely consist of the track/sector
  # of the file
  #  	
  def compute(self):
    for n in range(self.nbfile):
       self.filelist[n].compute()   

  def extractSec(self,track,sec,maxi=256):
    st = ""
    off= self.sectOffset(track,sec)
    for n in range(maxi):
      st = st+ hex(self.getByte(off+n)+256)[3:].upper()
    return st 
         
class CATENTRY:
  def __init__(self,typ,trkT,secT,siz,name):
    self.typ    = typ &0xf
    self.trkT   = trkT
    self.secT   = secT
    self.name   = name
    self.siz    = siz
    self.seclist = []
  
  #
  # descripting string
  #  
  def get(self):
    st = filetype[self.typ &0xf]+"   "+("     "+str(self.siz))[-5:]+"  "
    st = st+self.name
    return st
  
  #
  # display information (name+ seclist)
  #  
  def display(self):
    print self.get()  
    for n in self.seclist:
      print n.get()
  #
  # get the trk/sec list of the file
  #
  def compute(self):
    #self.display()
    off = disk.sectOffset(self.trkT,self.secT)
    ctrk = self.trkT
    csec = self.secT
    while ((ctrk!=0) or (csec!=0)):
      #dumpSec(ctrk,csec)
      off = disk.sectOffset(ctrk,csec)
      ctrk = disk.getByte(off+1)
      csec = disk.getByte(off+2)
      off = off+12
      nb = 0
      while ((nb<122) and (disk.getByte(off) != 0)):
        #print ord(res[off]),"/",ord(res[off+1])
	self.seclist.append(TRKSEC(disk.getByte(off),disk.getByte(off+1)))
	off += 2
	nb+=1

  def extract(self):
    st = ""
    for n in self.seclist:
      st += disk.extractSec(n.trk,n.sec)
    #print st
    if (self.typ == 2):
      ln = int(st[2:4]+st[0:2],16)+3
      print ln
      preamb ="****"+st[0:4]+"*****"
      #print preamb+st[4:ln*2]
      return preamb+st[4:ln*2]
    if (self.typ == 4):
      ln = int(st[6:8]+st[4:6],16)+8
      
##    print ln 
##    print st[0:ln*2]
    return st    


class TRKSEC:
  def __init__(self,trk,sec):
    self.trk =trk
    self.sec =sec
    
  def get(self):
    return ("00"+str(self.trk))[-2:]+'/'+("00"+str(self.sec))[-2:]  
            
filetype = {0:"TEXT",1:"IB  ",2:"ASB ",4:"BIN "}
disk = DSK()
def parse():
  parser = argparse.ArgumentParser()
  parser.add_argument('-fn',action='store',default=None)
  args = parser.parse_args()
  return [args.fn]

def sectOffset1(track,sec):
  return (track*16+sec)*256

def dumpSec(track,sec):

  off= sectOffset(track,sec)
  for i in range(16):
    st = hex(i+256)[3:]+" : "
    ascst = "   "
    for j in range(16):
      st = st+ (disk.getByte(off)+256)[3:].upper()
      if ((disk.getByte(off) & 0x7f)>31):
        ascst+=chr(disk.getByte(off)&0x7F)
      else:
        ascst+=" "	
      off += 1
    print st+ascst

def extractSec1(track,sec,maxi=256):
  st = ""
  off= sectOffset(track,sec)
  for n in range(maxi):
    st = st+ hex(ord(res[off+n])+256)[3:].upper()
  return st  
       
def printDir():
  global disk
  
  off= disk.sectOffset(17,15)
  off = off+11
  while (disk.getByte(off) !=0):
    track = disk.getByte(off)
    sec   = disk.getByte(off+1) 
    typ   = disk.getByte(off+2)
    size  = disk.getByte(off)+33+disk.getByte(off+34)*256
    off = off+3
    st1 = filetype[typ &0xf]+"   "+("     "+str(size))[-5:]+"  "
    st = ""
    for i in range(28):
      st += chr(disk.getByte(off)&0x7F)
      off+=1
#    print st1+st
    off+=4
    disk.addEntry(typ,track,sec,size,st)
    
    
    
if (__name__=="__main__"):
  [fn] = parse()
  print fn
  fi = open(fn,mode="rb")
  res = fi.read()
  disk.read(fn)
  #print (res.decode("utf-8"))
  #print (len(res))
  #print ord(res[0])
  #print (sectOffset(0x0,0)) 
  printDir()
  
  disk.dispDir()
  
  disk.compute()
  na = raw_input("File to export ")
  na1 = (na+" "*28)[0:28]
  index = disk.findfile(na1)
  if (index != -1):
    ##print disk.filelist[index].extract()
    fnout = na+".out"
    fout = open(fnout,"w")
    fout.write(disk.filelist[index].extract())
    fout.close()
##  disk.filelist[0].display()
##  disk.filelist[1].extract()
##  dumpSec(18,14)
  
