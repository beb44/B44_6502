##
## appleII save and load interface
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
def parse():
  parser = argparse.ArgumentParser()
  parser.add_argument('-fn',action='store',default=None)
  parser.add_argument('-dev',action='store',default='/dev/ttyUSB0')
  parser.add_argument('-w',action='store_true')
  args = parser.parse_args()
  return [args.fn,args.dev,args.w];

##
## skip char until header begins
##

def HeadW(ser):
  c = ser.read()
  while (c != "*"):
    c = ser.read()

##
## strip the **** header
## and return the first char
##
def HeadR(fi,ser):
  c = ser.read()
  fi.write(c);
  while (c == "*"):
    c = ser.read()
    fi.write(c)
  return c
##
## reads n char from the serial interface
## transfer them to the dest file
## return the string compose of all this char
##
def ReadN(fi,ser,n):
  st = ""
  for i in range(0,n):
    c = ser.read() ## read spare
    fi.write(c)
    st += c
  return st


def WriteN(fi,ser,n):
  st = ""
  for i in range(0,n):
    c = fi.read(1) 
    ser.write(c)

##
## reads data from the serial interface in the pseudo
## appleII save/write mode
##
## first part is the header that indicates the length
## of data stream
## second part is the data part
##
def getFile(fn,ser):
  try:
    fi = open(fn,"wb")
  except:
    print "Unable to open "+fn+" in write mode"
    return -1
  ser.write("SAVE\r")
  HeadW(ser)
  c = HeadR(fi,ser)
  ##
  ## start of file is composed of three byte
  ## lenl lenh 55
  ##
  bl = c+ReadN(fi,ser,1)
  d = ReadN(fi,ser,2)
  print d+bl
  leng = int(d+bl,16)+6
  print leng
  leng *=2
  c = ser.read() ## read spare
  fi.write(c)
  c = HeadR(fi,ser)
  while (leng != 0):
    if ((leng % 1000)==0):
      print '.'+chr(7),
      sys.stdout.flush()
    c = ser.read() 
    fi.write(c)
    leng -= 1
  print
  fi.close()
    
def putFile(fn,ser):
  try:
    fi = open(fn,"rb")
  except:
    print "Unable to open "+fn+" in read mode"
  ser.write("LOAD\r")
  #
  # strip head fisrt part
  #
  c='*'
  while (c == '*'):
    c=fi.read(1)
    ser.write(c)
    print c
    print (c=='*')
  st = c
  for n in range(0,3):
    c=fi.read(1)
    ser.write(c)
    st=st+c
  print st
  #
  # get data length
  #
  leng = int(st[2:4]+st[0:2],16)+6 
  #
  # get spare byte
  #
  WriteN(fi,ser,2)
  #
  # start of second section
  #
  c="*"
  while (c == '*'):
    c=fi.read(1)
    ser.write(c)
  #
  # write data
  # 
  WriteN(fi,ser,leng*2)
  fi.close()

if (__name__=="__main__"):
  fn,dev,w = parse()
  ##
  ## open device
  ##
  try:
    ser =serial.Serial(dev,9600);
  except:
    print "unable to open device "+dev
    exit(0)
  if (w):
    putFile(fn,ser)
  else:
    getFile(fn,ser)
