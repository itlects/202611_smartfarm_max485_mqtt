// UNO node: set NODE_ID to 1 or 2 before upload. 9600 baud, CRC16 ASCII protocol.
#include <SoftwareSerial.h>
#define NODE_ID 1
SoftwareSerial bus(10,11); // RX RO, TX DI
const byte DIR=2,PUMP=6,L1=4,L2=5,B1=7,B2=8,BUZZ=9;
char line[110], lastId[17]="boot"; byte pos=0, leds=0;
unsigned long lastPoll=0,pumpStart=0,lastButton=0;
bool pumping=false,prev1=HIGH,prev2=HIGH;
uint16_t crc(const char* p){uint16_t c=0xFFFF;while(*p){c^=(byte)*p++;for(byte i=0;i<8;i++)c=(c&1)?(c>>1)^0xA001:c>>1;}return c;}
void pump(bool on){pumping=on;digitalWrite(PUMP,on);if(on)pumpStart=millis();}
void outputs(){digitalWrite(L1,leds&1);digitalWrite(L2,leds&2);}
void reply(){char body[85],out[100];snprintf(body,sizeof(body),"S,%d,%s,%d,%d,%d",NODE_ID,lastId,analogRead(A0),pumping,leds);snprintf(out,sizeof(out),"%s*%04X\n",body,crc(body));digitalWrite(DIR,HIGH);delayMicroseconds(100);bus.print(out);bus.flush();delayMicroseconds(1200);digitalWrite(DIR,LOW);}
void receive(){char* star=strchr(line,'*');if(!star||strlen(star+1)!=4)return;*star=0;if(crc(line)!=strtoul(star+1,NULL,16))return;
 int n,p,l; char id[17];
 if(sscanf(line,"Q,%d",&n)==1&&line[0]=='Q'&&n==NODE_ID){lastPoll=millis();reply();}
 else if(sscanf(line,"C,%d,%16[^,],%d,%d",&n,id,&p,&l)==4&&n==NODE_ID&&(p==0||p==1)&&l>=0&&l<4){lastPoll=millis();if(strcmp(id,lastId)!=0){strncpy(lastId,id,sizeof(lastId)-1);leds=l;outputs();pump(p);}reply();}
}
void setup(){pinMode(DIR,OUTPUT);digitalWrite(DIR,LOW);pinMode(PUMP,OUTPUT);pump(false);pinMode(L1,OUTPUT);pinMode(L2,OUTPUT);pinMode(B1,INPUT_PULLUP);pinMode(B2,INPUT_PULLUP);if(NODE_ID==1)pinMode(BUZZ,OUTPUT);bus.begin(9600);}
void loop(){while(bus.available()){char c=bus.read();if(c=='\n'){line[pos]=0;receive();pos=0;}else if(c!='\r'){if(pos<sizeof(line)-1)line[pos++]=c;else pos=0;}}
 unsigned long now=millis();if(pumping&&(now-pumpStart>=5000||now-lastPoll>=3000))pump(false);
 if(now-lastButton>=35){lastButton=now;bool a=digitalRead(B1),b=digitalRead(B2);if(prev1&&!a){pump(false);leds^=1;outputs();if(NODE_ID==1)tone(BUZZ,1800,80);}if(prev2&&!b){leds^=2;outputs();}prev1=a;prev2=b;}
}
