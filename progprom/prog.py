import sys,serial
import argparse

rw ='W'
#
# checks the number of argument (1) and return
# its value 
def getFN():
  if (len(sys.argv) != 2):
    print "syntax is python prog.py <fileneme>"
    return ""
  return sys.argv[1]

#
# decode one hexadecimal digit
#
def readNibble(val):
  if ((val>='0') and (val<='9')):
    return ord(val)-ord('0')
  if ((val>='A') and (val<='F')):
    return 10 + (ord(val)-ord('A'))
  return 0

def getNibble(val):
  return (('0'+hex(val)[2:])[-2:]).upper()
#
# decode one hexadecimal byte
#
   
def readByte(val):
  return (readNibble(val[0])<<4)+readNibble(val[1])
  
def ReadWord(val):
  return (readByte(val[0:2])<<8)+readByte(val[2:4])
    
def parseFile(fn):
  fi = open(fn)
  for n in fi.readlines():
    if (n[0] != 'S'): continue
    if (n[1] == '9'):
      print "End record Found"
      break
    if (n[1] == '1'):
      # data record found
      #get number of byte
      print "nb record ",n[2:4],readByte(n[2:4]),
      nb = readByte(n[2:4])
      cksum = readByte(n[2:4])+readByte(n[4:6])+readByte(n[6:8])
      print hex(ReadWord(n[4:8])),
      for p in range(4,readByte(n[2:4])+1):
        print hex(readByte(n[p*2:p*2+2])),  
        cksum += readByte(n[p*2:p*2+2])
      cksum += readByte(n[2+nb*2:2+nb*2+2])	
      if ((cksum & 0xff) == 0xff):
        print "OK"
      else:
        print "KO"	  	
  fi.close()

def readmode():
  global rw;
  
  rw='R'
  

def writeEEprom(fn):
  fi = open(fn)
  for n in fi.readlines():
    print n,
    ser.write(n+'\r') ## write cuurent srecord
    s = ser.read()
    #print s
    while (s != '>'):
      #print s,
      s = ser.read()
      
def readEEprom(start,stop):
  res= '';
  st = start & 0xfff0
  while (st <stop):
    #print getNibble(st>>8)+getNibble(st & 0xff)
    str ="R113"+getNibble(st>>8)+getNibble(st & 0xff)
    ##print str
    ser.write(str+'\n\r');
    s = ser.read()
    while (s != '>'):
      if (s != '>'): res =res+s;
      s = ser.read()
    st += 16;
    print res[:-2]
    res = '';
    
          
parser = argparse.ArgumentParser() 
parser.add_argument('-fn',action='store',default=None)
parser.add_argument('-r', action='store_true')  # on/off flag
parser.add_argument('-s', action='store') # start address
parser.add_argument('-t', action='store') # start address
args = parser.parse_args()
print args.fn, args.r,args.s,args.t
   
fn=  args.fn
if ((fn == None) and (args.r == False)):
  print "Missing filename for write mode"
  exit(0);
#parseFile(fn)
## open serial port
ser =serial.Serial('/dev/ttyUSB0',9600);
## wait for prompt
s = ser.read()
while (s != '>'):
  # print s
  s = ser.read()
##print s
if (args.r == False):
  ## programmation mode
  writeEEprom(fn)
else:
  if (args.s == None):
    start = 0
  else:
    start = int(args.s,0)
  print "start : ",start
  if (args.t == None):
    stop = 0
  else:
    stop = int(args.t,0)
  print "stop : ",stop
  readEEprom(start,stop)
  
  None
exit(0)    
for n in fi.readlines():
  if args.r: 
    print 'R'+n[1:]
  print '----',n
  if args.r:
    ser.write('R'+n[1:]+'\r')
  else:
    ser.write(n+'\r')
  s = ser.read()
  while (s != '>'):
    print s,
    s = ser.read()
  print
    
