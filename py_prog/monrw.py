##
## appleII read and write interface
##
## It replaces the original tape with 
## a text file
##
##
import sys,serial
import argparse
import time

##
## parse input line
##
## -fn <filename> is the file where data are read
##                or write
## -dev <dev>     is the USB port connected to serial
##                interface
## -w             selects reception mode (SAVE from
##                Apple II perspective
## -s <addr>      start address
## -t <addr>      end address 
def parse():
  parser = argparse.ArgumentParser() 
  parser.add_argument('-fn',action='store',default=None)
  parser.add_argument('-dev',action='store',default='/dev/ttyUSB0')
  parser.add_argument('-w',action='store_true')
  parser.add_argument('-s',action='store',default=None)
  parser.add_argument('-t',action='store',default=None)
  args = parser.parse_args()
  return [args.fn,args.dev,args.w,args.s,args.t];


def getFile(fn,start,stop):
  try:
    fi = open(fn,"wb")
  except:
    print "Unable to open "+fn+" in write mode"
    return -1
  ser.write("%4x.%4x"%(start,stop));
  ser.write(chr(0x19)+"W\r")
  c = ser.read()
  while ( c != "*"):
   c = ser.read()
  while ( c == "*"):
   c = ser.read()
  fi.write(c)
  fi.write(ser.read())
  start +=1
  while(start<=stop):
    c = ser.read()
    fi.write(c)
    c = ser.read()
    fi.write(c)
    start+=1
  fi.close()

def putFile(fn,start,stop):
  try:
    fi = open(fn,"rb")
  except:
    print "Unable to open "+fn+" in write mode"
    return -1
  ser.write("%4x.%4x"%(start,stop));
  ser.write(chr(0x19)+"R\r")
  for i in range(1,5):
    ser.write("*")
  while(start<=stop):
    ser.write(fi.read())
    ser.write(fi.read())
    start+=1
  fi.close()

if (__name__=="__main__"):
  fn,dev,w,start,stop  =  parse()
  ##
  ## open device
  ##
  try:
    ser =serial.Serial(dev,9600);
  except:
    print "unable to open device "+dev
    exit(0)
  ##
  ## check start and to parameter
  ##
  if (start == None):
    print "missing starting address"
    exit(0)
  if (stop  == None):
    print "missing end address"
    exit(0)
  ##
  ## converts address in int (from string)
  ##
  try:
   startv =  int(start,0)
   stopv  =  int(stop,0)
  except:
    print "incorrect start or stop address"
    pass
  if (start>stop):
    print "start location must be less than stop location"
    exit(0)
  if (w):
    putFile(fn,startv,stopv)
    pass
  else:
    getFile(fn,startv,stopv)
