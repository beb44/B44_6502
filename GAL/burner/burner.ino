
#define VERSION "ATF/GAL16V8 programmer v1.0"
// le portb est utilisé pour les bit RG
// ceci permet une afftectation directe

#define rgmask 0b001111111
#define sdin   2
#define sdout  3
#define clk    4
#define strb   5

#define edit   6
#define pv     7

#define vcc    A1
#define probe  A7
//
// macro definition
//
#define clk_low   {digitalWrite(clk,LOW);  }
#define clk_high  {digitalWrite(clk,HIGH); }
#define strb_low  {digitalWrite(clk,LOW);  }
#define strb_high {digitalWrite(clk,HIGH); }
#define pv_on     {digitalWrite(pv,HIGH); }
#define pv_off    {digitalWrite(pv,LOW); }
#define edit_on   {digitalWrite(edit,HIGH); delay(100); }
#define edit_off  {digitalWrite(edit,LOW);  delay(100); }
#define vcc_on    {digitalWrite(vcc,HIGH); delay(100); }
#define vcc_off   {digitalWrite(vcc,LOW);  delay(100); }
// input buffer
char test[]="3200643132333435363738";
char inp[128];
byte index;
// data buffer is 512 bit long
byte    dbuff[32]; 

int     t_strb;   // temporosation for strobe
int     t_clkw;   // temporisation clock ecriture
int     t_erase;  // temporisation strobe erase
int     old_millis;
bool    editforced;
bool    debug;
bool    read_VPP;

const byte bitmask[8] = {0x80,0x40,0x20,0x10,0x08,0x04,0x02,0x01}; 

void setup() {
  // tous les RG a zero
  PORTB &= ~rgmask;
  // D8..D13 output
  DDRB  |=  rgmask;

  pinMode(sdin,OUTPUT);  // sdin  Input  du point de vue GAL
  pinMode(sdout,INPUT);  // sdout Output du point de vue GAL
  clk_low
  pinMode(clk,OUTPUT);
  strb_high
  pinMode(strb,OUTPUT);
  // turn PV off
  pv_off
  pinMode(pv,OUTPUT);
  // turn edit off
  editforced = false;
  edit_off
  pinMode(edit,OUTPUT);
  vcc_off
  pinMode(vcc,OUTPUT);
  
  
  t_strb  = 40;          // defaut value
  t_erase = 80;          // defaut value
  t_clkw  = 100;         // defaut value
   
  // input buffer int
  index   = 0;
  Serial.begin(9600);
  Serial.println(VERSION);
  
  debug=false;
  
  old_millis = millis()/1000;
  read_VPP   = false;
}
void Pread_VPP()
{
  float value = ((float)analogRead(probe))*160/887;
  Serial.println(value);
}  
//
// hex to ascii routines
//
char Nibble(byte v)
{
  if ((v>=0) && (v<=9))   return '0'+v;
  if ((v>=10) && (v<=15)) return 'A'+(v-10);
  return '0';
}


//
// ascii to hex or dec routines
//


int deg1digit(char d2,char d1)
{
  int val = 0;
  if ((d2>='0') && (d2<='9'))
    val = (d2-'0')*10;
  if ((d1>='0') && (d1<='9'))
    val += (d1-'0');
  return val;  
}

byte ascToNibble(char c)
{
  if ((c>='0') && (c<='9')) return c-'0';
  if ((c>='A') && (c<='F')) return c-'A'+10;
  if ((c>='a') && (c<='f')) return c-'a'+10;
  return 0;
}

byte ascToByte(char c1,char c2)
{
  return (ascToNibble(c1)<<4) + ascToNibble(c2);
}
//
// strobe data and row
//
void Strobe(int tempo)
{
  digitalWrite(strb,LOW);
  delay(tempo); 
  digitalWrite(strb,HIGH);
  
}
//
// produce one clik tick for read operation
//
void TickR()
{
  digitalWrite(clk,HIGH);
//  delayMicroseconds(100); 
  digitalWrite(clk,LOW);
//  delayMicroseconds(100); 
}

//
// produce one clik tick for write operation
//
void TickW()
{
  digitalWrite(clk,HIGH);
  delay(1); 
  digitalWrite(clk,LOW);
  delay(1); 
}
//
// send one bit to sdin
//
void sendBit(byte on)
{
  //Serial.println(on);
  digitalWrite(sdin,(on?HIGH:LOW));
  TickW();
}
//
// sends out num bits contained in dbuff
//
void sendBits(unsigned short num)
{
  byte p;
  byte off;
  byte data;
  p = 0; off =0; 
  data = dbuff[off]; // load first 8 bits in data
  while (num > 0)
  {
    sendBit(data & bitmask[p]); // msb first
    num--; p++;
    if (p == 8)
    {
      // load next 8 bits in data
      data = dbuff[++off];
      p = 0;
    }
  } 
}

//
// read one bit on sdout
//
bool recvBit()
{
  bool val = (digitalRead(sdout)==HIGH);
  TickR();
  return val;
}
//
// receives num bits from sdout
//
int recvBits(unsigned short num)
{
  byte p;
  byte off;
  byte data;
  p = 0; off =0; data = 0; 
  while (num > 0)
  {
    if (recvBit()) data |= bitmask[p];
    num--; p++;
    if (p == 8)
    {
      dbuff[off++] = data; // store 8 bits
      p = 0;
      data = 0;
    }
  } 
  if (p!=0) dbuff[off++]= data;
  return off;  // return number of effective bytes
}
//
// set RG
//
void setRG(byte RG)
{
  PORTB = (PORTB & ~rgmask) | (RG & rgmask);
}

//
// gal init sequence
//
void turnOn()
{
  Serial.println("Turn ON");
  edit_off
  pv_off
  setRG(0x3F); // ????
  clk_high
  strb_high
  digitalWrite(sdin,HIGH);
  delay(100);
  vcc_on
  delay(100);
  clk_low
  delay(200);  
  if (editforced) edit_on
}
void turnOff()
{
  Serial.println("Turn OFF");
  delay(100);
  pv_off
  setRG(0x3F); // ????
  digitalWrite(sdin,HIGH);
  edit_off
  pv_on
  delay(20);
  pv_off  
}
//
// read num bits from a given RG
//
byte readRG(byte RG,unsigned short num)
{
  pv_off        // set read mode
  delay(100);
  setRG(RG);
  Strobe(t_strb);     // strobe RG
  delay(100);
  return recvBits(num);
}
//
// write num btis to a given RG
//
void writeRG(byte RG,unsigned short num)
{
  pv_on        // set write mode
  delay(100);
  setRG(RG);
  delay(100);
  sendBits(num);
  delay(100);
  if (RG==63)
    Strobe(t_erase);    // strobe RG and data
  else
    Strobe(t_strb  );  
  delay(100);
  pv_off       // reset pv
  
}

void printPES()
{
char outbuf[20];
byte p=0;

  for(int i=0;i<8;i++) dbuff[i]='X';
  readRG(58,82);
  for (int i=0;i<8;i++) 
  { 
    inp[p++]= Nibble(dbuff[i]>>4);
    inp[p++]= Nibble(dbuff[i] & 0x0f);
  }
  outbuf[p]=0;
  Serial.println(inp);
}

//
// lecture des fusibles
//
void readfuse(char *buff)
{
  // 1er champ (2 bytes) numero de rang
  int rg = deg1digit(*(buff),*(buff+1));
  buff += 2;
  if (debug)
  {
    Serial.print("Rang = ");
    Serial.println(rg);
  }  
  // 1er champ (4 bytes) numero de rang
  int len = deg1digit(*(buff),*(buff+1))*10+
            deg1digit(*(buff+2),*(buff+3));
  buff += 4; 
  if (debug)
  {
    Serial.print("Len  = ");
    Serial.println(len);
  }
  // lecture des bits
  if (not(editforced)) edit_on
  delay(200);
  int off = readRG(rg,len);
  if (not(editforced)) edit_off
  delay(200);
  for (int i=0;i<off;i++)
  {
    *buff++ =  Nibble(dbuff[i]>>4);
    *buff++ =  Nibble(dbuff[i]& 0x0f);
  }  
  *buff = 0;
  Serial.println(inp);  
}
//
// ecriture de fusible
//
void writefuse(char *buff)
{
  // 1er champ (2 bytes) numero de rang
  int rg = deg1digit(*(buff),*(buff+1));
  buff += 2;
  if (debug)
  {  
    Serial.print("Rang = ");
    Serial.println(rg);
  }  
  // 1er champ (4 bytes) numero de rang
  int len = deg1digit(*(buff),*(buff+1))*10+
            deg1digit(*(buff+2),*(buff+3));
  buff += 4;
  if (debug)
  {
    Serial.print("Len  = ");
    Serial.println(len);
  }
  // transfert des data en hexa dans dbuff
  for (int i=0;i<=len;i=i+8)
  { 
    dbuff[i/8] = ascToByte(*(buff),*(buff+1));
    if (debug)
    {
      Serial.print(i);
      Serial.print(" - ");
      Serial.println(dbuff[i/8],HEX);
    }  
    buff +=2; 
  }
  
  // trandfert des données
  if (not(editforced)) edit_on
  delay(2000);
  writeRG(rg,len);
  delay(1000);
  if (not(editforced)) edit_off
}

void setEdit(char *buff)
{
  if (*buff == '1')
  {
    editforced= true;
    edit_on
  }
  else
  {
    editforced= false;
    edit_off
  }
}
void setInit(char *buff)
{
  if (*buff== 'N') // 'ON'
    turnOn();
  if (*buff== 'F') // 'ON'
    turnOff();
}
void experiment()
{
  for (int i=1;i<20;i++)
  {
    Serial.print("Erase time = ");
    Serial.println(i*10);
    t_erase = i*10;
    dbuff[0]= 255;
    writeRG(63,1);
    for (int j=1;j<20;j++)
    {
      Serial.print("  read time = ");
      Serial.println(j*10);
      t_strb =j*10;
      readRG(0,64);
      if (dbuff[0] == 255)
      {
        Serial.print("Succes ");
        Serial.print(i*10);
        Serial.print(" ");
        Serial.println(j*10);
        return;
      }    
    }
  }
}  
//
// traitement des commandes
//
void parseinp(char *buff)
{
  //Serial.println(buff);
  switch (*buff)
  {
    case 'R': readfuse(++buff);       break;  // lecture
    case 'S': writefuse(++buff);      break;  // ecriture
    case 'T': writefuse(test);        break;  // test string
    case 'E': setEdit(++buff);        break;  // edit en mode force ou non
    case 'O': setInit(++buff);        break;   
    case 'V': read_VPP= ! read_VPP;   break;   
    case 'X': experiment();           break;
  }  
}
void loop() {
  // put your main code here, to run repeatedly:
  if (millis()/1000 != old_millis)
  {
    old_millis = millis()/1000;
    if (read_VPP==true) Pread_VPP();
  }  
  if (Serial.available())
  {
    char c =Serial.read();
    inp[index++] = c;
    if ((c == '\n') || (c == '\r'))
    {
      parseinp(inp);
      index = 0;
    }
  }
}
