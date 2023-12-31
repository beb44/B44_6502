from xml.sax.handler import ContentHandler
import xml.sax
import argparse
import time
import sys,serial
ser = None
#
# Input port description
#
class Sportmap:
  def __init__(self,pos,neg):
    self._pos = pos  ## direct  entry column
    self._neg = neg  ## negated entry column
#
# Output port description
#

class Dportmap:
  def __init__(self,stAddr,xorOffset,ac1Offset):
    self._stAddr     = stAddr      ## first addr
    self._xorOffset  = xorOffset   ## xor offset
    self._ac1Offset = ac1Offset  ## ac1 offset
#
# GAL16V08 Mappping 
#    
INPUTS  = {"P1"  :Sportmap(2,3)  ,
           "P2"  :Sportmap(0,1)  ,# [ 0, 1],
           "P3"  :Sportmap(4,5)  ,# [ 4, 5],
           "P4"  :Sportmap(8,9)  ,# [ 8, 9],
           "P5"  :Sportmap(12,13), # [12,13],
           "P6"  :Sportmap(16,17), # [16,17],
           "P7"  :Sportmap(20,21), # [20,21],
           "P8"  :Sportmap(24,25), # [24,25],
           "P9"  :Sportmap(28,29), # [28,29],
           "P11" :Sportmap(30,31), # [30,31],
           "P12" :Sportmap(26,27), # [26,27],
           "P13" :Sportmap(22,23), # [22,23],
           "P14" :Sportmap(18,19), # [18,19],
           "P17" :Sportmap(14,15), # [14,15],
           "P18" :Sportmap(10,11), # [10,11],
           "P19" :Sportmap(6,7)    # [ 6, 7]}
	   }
OUTPUTS = {"P19": Dportmap(0,0,0)   , # [   0,0,0],
           "P18": Dportmap(256,1,1) , # [ 256,1,1],
	   "P17": Dportmap(512,2,2) , # [ 512,2,2],
	   "P16": Dportmap(768,3,3) , # [ 768,3,3],
	   "P15": Dportmap(1024,4,4), # [1024,4,4],
	   "P14": Dportmap(1280,5,5), # [1280,5,5],
	   "P13": Dportmap(1536,6,6), # [1536,6,6],
	   "P12": Dportmap(1792,7,7)  # [1792,7,7]
	   }

OUTPUTLIST = ["P19","P18","P17","P16","P15","P14","P13","P12"]
#
# config map GAL16V8AB
#
V168AB = [
      	  0,1,2,3,
      	  145,
      	  72,73,74,75,
      	  80,81,82,83,84,85,86,87,
          88,89,90,91,92,93,94,95,
          96,97,98,99,100,101,102,103,
          104,105,106,107,108,109,110,111,
          112,113,114,115,116,117,118,119,
          120,121,122,123,124,125,126,127,
          128,129,130,131,132,133,134,135,
          136,137,138,139,140,141,142,143,
      	  76,77,78,79,
      	  144,
      	  4,5,6,7
	 ]

invbmap = [128,64,32,16,8,4,2,1]

assign = {}		# list association input -> port
destport = None		# port de sortie courant
destline = None		# product term courant (rela. port)
linemask = None		
ssig     = None
fsig     = None
fusemap  = list('1'*2194);
L2048    = list('1'*8)  # default active HIGH
L2120    = list('1'*8)  # default OUTPUT
PT       = list('0'*64) # used product terms

xorBase  = 2048		# base XOR
ac1Base  = 2120		# base ac1
cfgBase  = 2048		# base RG config
ptBase   = 2128		# base product terms
ac0Base  = 2193		#  bit address
synBase  = 2192		# SYN bit address
state    = None		# AND/NAND handling state

ser = None

#
# Parser XML
#
class Extract(xml.sax.handler.ContentHandler):
  def __init__(self):
    pass
  
  def startElement(self,name,attrs):
    global destport,destline,linemask,ssig,fsig,state

    if (state == "set"):
      if (name in assign):
	stAddr   = OUTPUTS[destport]._stAddr
	subAddr = (ord(destline)-ord('0'))*32
	index = INPUTS[assign[name]]._pos
        fusemap[stAddr+ subAddr + index] = '0'
	#print destport,destline,name
      else:
        print "non existent input",name,destport,destline
      return
      

    if (state == "reset"):
      if (name in assign):
	stAddr   = OUTPUTS[destport]._stAddr
	subAddr = (ord(destline)-ord('0'))*32
	index = INPUTS[assign[name]]._neg
        fusemap[stAddr+ subAddr + index] = '0'
      else:
        print "non existent input",name,destport,destline
      return
       
    if (name == "GAL"):
      if ("SIG" in attrs):
        ssig = "*L2056 "+ (''.join(format(ord(i), '08b') for i in attrs["SIG"]))
        fsig =  attrs["SIG"]
	print fsig
      if ("AC0" in attrs):
	fusemap[ac0Base] = attrs["AC0"]  
      if ("SYN" in attrs):
	fusemap[synBase] = attrs["SYN"]  
      return
	
    if (name == "ASSIGN"):
      if (("SRC" in attrs) and ("NAME" in attrs)):
        if (attrs["SRC"] in INPUTS.keys()):
	  assign[attrs["NAME"]] = attrs["SRC"]
	else:
	  print "source port "+attrs["SRC"]+" does not exists"  
      else:
        print "missing argument in ASSIGn statement"
      return
      
    if (name == "COMBINE"):
      if ("DEST" in attrs):
        if (attrs["DEST"] in OUTPUTS):
	  destport = attrs["DEST"]
	else:
	  print "destination "+attrs["DEST"]+" does not exists"
	  return        
      if ("XOR" in attrs):
        offset = OUTPUTS[destport]._xorOffset
        if (attrs["XOR"] == "1"):
          L2048[offset] = '1'
	  fusemap[xorBase+offset] = '1' 
        else:
          L2048[offset] = '0' 
	  fusemap[xorBase+offset] = '0' 
      if ("AC1" in attrs):
        offset = OUTPUTS[destport]._ac1Offset
	print  ac1Base+offset
        if (attrs["AC1"] == "1"):
          L2120[offset] = '1'
	  fusemap[ac1Base+offset] = '1' 
        else:
          L2120[offset] = '0' 
	  fusemap[ac1Base+offset] = '0' 
      return

    if (name == "LINE"):
      if ("NUM" in attrs):
        if (attrs["NUM"] in ["0","1","2","3","4","5","6","7"]):
          if (destport == None):
	    print "destport not defined"
	  else:
	    destline = attrs["NUM"]
	    linemask =list("1"*32) 
        else:
          print "Illegal line number "+attrs["NUM"]
      else:
        print "Missing line number"	  	
      return

    if ((name == "AND") or (name=="NAND")):
      if ((destline == None) or (destport == None)):
        print "Missing line or destination port"
	return
      if (name =="AND"): 
        state = "set"
      else:
        state = "reset"
      return		

  def endElement(self,name):
    global destport,destline,state

    if (name == "COMBINE"):
      destport = None

    if (name == "LINE"):
      offset = OUTPUTS[destport]._stAddr/32+(ord(destline)-ord('0'))
      PT[offset]='1'
      fusemap[ptBase+offset]='1'
      destline = None
      state = None

    if ((name == "AND") or (name == "NAND")) :
      state = None

  def process(self):
    pass

#
# process xml file content
#
def process(fn):
  parser = xml.sax.make_parser()
  handler = Extract()
  parser.setContentHandler(handler)
  parser.parse(fn)
  return handler.process()

#
# set all product terms as unused
#
def setPt():
  for i in range(0,64):
    fusemap[ptBase+i]='1'

#
# print fuse table (port only)
#
def prtFuseMap():
  global fusemap
  Addr = 0
  for n in range (0,8):
    print OUTPUTLIST[n]+"  XOR "+fusemap[xorBase+n]+ " AC1 "+ fusemap[ac1Base+n]
    for p in range  (0,8):
      if (PT[n*8+p ] == "1"):
        print ("".join(fusemap[Addr:Addr+32])).replace('1','-').replace('0','X')
      Addr+=32
      
def prtJedec():
  global fusemap
  print "*F0"
  print "*G0"
  print "*QF2194"
  Addr = 0
  k = 0
  for n in range (0,8):
    for p in range  (0,8):
      if (PT[n*8+p] == "0"):
	pass
        #print ("*L%04d "%Addr)+"0"*32
      else:
        print ("*L%04d "%Addr)+"".join(fusemap[Addr:Addr+32])
      Addr += 32
      k +=1
  S="*L2056 "
  p = 0
  for n in fsig:
    if p>7: break
    S = S+("000000000"+bin(ord(n))[2:])[-8:]
    p += 1;
  while (p <8):
    S=S+"00"
    p+=1
  print S
  print "*L2048 "+"".join(fusemap[2048:2048+8])
  print "*L2128 "+"1"*64
  print "*L2120 "+"".join(fusemap[2120:2120+8])
  print "*L2192 "+fusemap[2192]
  print "*L2193 "+fusemap[2193]
def getLoadLine(rg):
  global fsig
  
  if (rg<32):
    #
    # fuses
    #
    S = "L%02d0064"%rg
    Addr = rg;
    for n in range(0,8):
      val = 0;
      for p in range(0,8):
        val <<= 1
        if ((fusemap[Addr]=='1') and (PT[n*8+p] == "1")): val += 1
	Addr += 32  
      S=S+"%02X"%val
    return S
  if (rg==32):
    #
    # UE fuse
    #
    S = "L320064"
    p = 0
    for n in fsig:
      if p>7: break
      S = S+"%02X"%ord(n)
      p += 1;
    while (p <8):
      S=S+"00"
      p+=1
    return S       

  if (rg==60):
    #
    # Config
    #
    S="L600082"
    p = 0
    val = 0
    for n in V168AB:
      val <<=1
      if (fusemap[cfgBase+n] == '1'): val +=1
      p += 1
      if (p==8):
        S=S+"%02X"%val
	val = 0
	p = 0
    if (p != 0):
      while (p<8):
        val <<=1
	p +=1	 
      S=S+"%02X"%val
    return S    
def prtRGlines():
  for i in range(0,32):
    print getLoadLine(i)
  print getLoadLine(32)
  print getLoadLine(60)

#
# waits for prompt
#
def waitPrompt():
  c = " "
  while (c != ">"):
    c = ser.read()

#
# send command
#
def sendCmd(st):
  global ser
#  waitPrompt()
#  print st
  ser.write(st+'\r')
#
# read result 
#
def getResp():
  st = ""
  c = ser.read() 
  while ((c!=chr(13)) and (c!=chr(10))):
    st = st+c
    c = ser.read()
  return st 

#
# verifyWrite operation
#
def verifyWrite(st,ve):
  return True
  sendCmd(st)
  return True
  rep = getResp().replace("R","S")
  return (ve in rep)
def writeGal():
  #
  # turn PAL in program mode
  #
  sendCmd("ON")
  time.sleep(5)
  #
  # erase content
  #
  sendCmd("S630001FF")
  time.sleep(1)
  #
  # write product terms
  #
  cont = True
  for i in range(0,32):
    if cont: 
      ve = getLoadLine(i).replace("L","S")
      sendCmd(ve)
      time.sleep(5)
      cont = verifyWrite( "R%02d0064"%i,ve) 
      if (cont == False):
       print "Error during write of line",ve
  #
  # write signature 
  #
  if cont:
    ve = getLoadLine(32).replace("L","S")
    sendCmd(ve)
    time.sleep(5)
    cont = verifyWrite("R320064",ve) 
    if (cont == False):
     print "Error during write of line",ve
  #
  # write configuration
  #
  if cont:
    ve = getLoadLine(60).replace("L","S")
    sendCmd(ve)
    time.sleep(5)
    cont = verifyWrite("R600082",ve) 
    if (cont == False):
     print "Error during write of line",ve
  #
  # turn off
  #
  sendCmd("OFF")

def readRG(str):
  sendCmd(str)    
  S = getResp()
  while ((S== "") or (S[0]!="R")):
    S = getResp()
  return S

def readGal():
  global fsig
  #
  # turn PAL in program mode
  #
  sendCmd("ON")
  getResp()
  S=readRG("R320064")
  S=readRG("R320064")
  fsig = [0,0,0,0,0,0,0,0]
  for p in range(0,8):
   fsig[p] = chr(int(S[7+p*2:7+p*2+2],16))
  print S
  time.sleep(5)
  for r in range(0,32):
    S = readRG("R%02d0064\n"%r)
    print S
    for n in range(0,8):
      v =  int(S[7+n*2:7+n*2+2],16)
      for i in range(0,8):
        if (invbmap[i]&v):
          fusemap[(i+n*8)*32+r] = "1"
          PT[n*8+i] = "1"
        else:
          fusemap[(i+n*8)*32+r] = "0"
  S = readRG("R600082")
  print S
  n = 0
  p = 0
  while (n<82):
    print S[7+p*2:7+p*2+2]
    v= int(S[7+p*2:7+p*2+2],16)      
    for i in range(0,8):
      if (invbmap[i]&v):
        fusemap[cfgBase+V168AB[n]] = "1"
      else:
        fusemap[cfgBase+V168AB[n]] = "0"
      n = n+1
      if (n==82):
        break
    p+=1
    
    
  #
  # turn off
  #
  sendCmd("OFF")

def args():
  parser = argparse.ArgumentParser()
  parser.add_argument('-fn',action='store',default=None)
  parser.add_argument('-dev',action='store',default='/dev/ttyUSB0')
  parser.add_argument('-pf',action='store_true')
  parser.add_argument('-pj',action='store_true')
  parser.add_argument('-pp',action='store_true')
  parser.add_argument('-r',action='store_true')
  parser.add_argument('-w',action='store_true')
  args = parser.parse_args()
  return [args.fn,args.dev,args.pf,args.pj,args.pp,args.r,args.w]

if __name__ == "__main__":
  fn,de,pf,pj,pp,r,w = args()
  print pp
  if (not(r)):
    # configuration not coming from the GAL
    if (fn == None) :
      print "No filename specified"
      exit(0)
    setPt()
    try:     
      process(fn)
    except:
      print "Error hanfling "+fn
      exit(0)
  else:
    print "Read configuration from gal"
    try:
      ser = serial.Serial(de,9600);
    except:
      print "Unable to open "+de
      exit(0)
    readGal()
  
  if (pf) :
    prtFuseMap()
  if (pj) :
    prtJedec()
  if (pp):
    prtRGlines();  
  if (w):
    try:
      ser = serial.Serial(de,9600);
    except:
      print "Unable to open "+de
      exit(0)
    print "programming  gal using "+de
    writeGal()
