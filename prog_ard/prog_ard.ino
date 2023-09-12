#define DATA   2
#define CLOCK  3
#define STROBE 4
#define DATA0  5
#define DATA7  12
#define RWB    13
byte  OE = HIGH;
byte lastData = 0xFF;

//  interface section
char buff[100];    // reception buffer
char *cptr;        // current char


void setup() {
  // put your setup code here, to run once:
  pinMode(DATA,OUTPUT);
  pinMode(CLOCK,OUTPUT);
  pinMode(STROBE,OUTPUT);
  digitalWrite(STROBE,HIGH);
  digitalWrite(RWB,HIGH);
  pinMode(RWB,OUTPUT);  
  Serial.begin(9600);
}

void resetDataPin()
{
  for (byte i=DATA0;i<=DATA7;i++)
    pinMode(i,INPUT);
}
void setData(byte data)
{
  for (byte i=DATA0;i<=DATA7;i++)
  {
    digitalWrite(i,(((data &0x01 ) == 1)?HIGH:LOW));
    pinMode(i,OUTPUT);
    data = data >> 1;
  }
}

byte getData()
{
  
 byte data = 0;
  for (byte i=DATA7;i>=DATA0;i--)
  {
    pinMode(i,INPUT);
    data = (data<<1) + (digitalRead(i)==HIGH?1:0);
  }
  return data;
}

void setAddr(unsigned int Addr,int OE)

{
  Addr = (OE==HIGH?(Addr | 0x8000):(Addr &0x7FFF));
  digitalWrite(STROBE,HIGH);  
  shiftOut(DATA,CLOCK,MSBFIRST,Addr>>8);
  shiftOut(DATA,CLOCK,MSBFIRST,Addr & 0xff);
  digitalWrite(STROBE,LOW);
  digitalWrite(STROBE,HIGH);
}

void writeData(unsigned int Addr,byte val)
{
  setAddr(Addr,HIGH);  // disable OUTPUT
  setData(val);
  delayMicroseconds(5); // wait effective data output disable
  digitalWrite(RWB,LOW); // set RWB to low to trigger write
  delayMicroseconds(2);  // Let the chip copy
  digitalWrite(RWB,HIGH);// Perform write
  delay(10); // rest time
  resetDataPin(); 
}

byte readData(unsigned int Addr)
{
  setAddr(Addr,LOW); // enable OUTPUT
  delay(1);          // wait for output to stabalise
  return getData();
}

byte asciiToHex(char c)
{
  return ((c<='9')?(byte)(c-'0'):(byte)(c-'A'+10));
}
byte getByte(char *buff)
{
  byte val;
  val = asciiToHex(*buff);
  buff++;
  val = (val << 4)+asciiToHex(*buff);
  return val;
}

char hexToAscii(byte val)
{
  return (val<=9?'0'+val:'A'+val-10);
}
void setByte(char *buff,byte val)
{
  *buff++ = hexToAscii(val>>4);
  *buff   = hexToAscii(val &0x0f);
}

void processWrite(char *buff)
{
byte data;

  buff++;   // skip to next chartacter
  if (*buff != '1')
  {
    Serial.println("Only S18 format allowed");
    return;
  }
  buff++;
  byte len = getByte(buff);  // get record len
  byte checksum = 0;
  buff += 2;
  byte lenH = getByte(buff); // get address MSB
  checksum += lenH;
  buff += 2;
  byte lenL = getByte(buff); // get address LSB
  checksum += lenL;
  buff += 2;
  
  unsigned int Addr = (lenH<<8)+lenL;
  byte nbbytes = len-3;
  for (int i=0;i<nbbytes;i++)
  {
    data = getByte(buff);
    writeData(Addr,data);
    checksum += data;
    buff += 2;
    Addr++;   
  }
  checksum += getByte(buff);
}
void processRead(char *buff)
{
byte data;

  buff++;   // skip to next chartacter
  if (*buff != '1')
  {
    Serial.println("Only S18 format allowed");
    return;
  }
  buff++;
  byte len = getByte(buff);  // get record len
  byte checksum = 0;
  buff += 2;
  byte lenH = getByte(buff); // get address MSB
  checksum += lenH;
  buff += 2;
  byte lenL = getByte(buff); // get address LSB
  checksum += lenL;
  buff += 2;
  
  unsigned int Addr = (lenH<<8)+lenL;
  byte nbbytes = len-3;
  for (int i=0;i<nbbytes;i++)
  {
    data = readData(Addr);
    setByte(buff,data);
    checksum += data;
    buff += 2;
    Addr++;   
  }
  *buff = 0;
    
}
void processCommand(char *buff)
{
  if (*buff == 'S')
  { 
    // write command
    processWrite(buff);
  }

  if (*buff == 'R')
  { 
    // write command
    processRead(buff);
    Serial.println(buff);
  }
}
void loop() {
  Serial.print(">");  // send prompt (ready to get next command)
  cptr =buff;
  while (true)
  {
    if (Serial.available() > 0)
    {
      *cptr = Serial.read();
      if (*cptr == 0xd) break;
      if (*cptr == 0) break;
      cptr++;
    }  
  }
  *++cptr='\0';
  // interpet received command
  processCommand(buff);
}
void loop_test() 
{
  // put your main code here, to run repeatedly:
  for (unsigned int i=0;i<=0x7FFF;i++)
  {
    writeData(i,(i&0xff));
    if (readData(i) != (i& 0xff))
    {
      Serial.print("Write or read error addr=");
      Serial.print(i,HEX);
      Serial.print(" expected value=");
      Serial.print((i&0xff),HEX);
      Serial.print(" Effective value=");
      Serial.println(readData(i));
      delay(10000);   // wait 10 seconds before next operation
    }
    else
    {
      Serial.print("Operation at address ");
      Serial.print(i,HEX);
      Serial.println(" OK");
    }
  }  
}
