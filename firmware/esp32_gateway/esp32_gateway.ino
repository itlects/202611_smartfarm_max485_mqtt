#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <time.h>
#include "secrets.h"
WiFiClient net; PubSubClient mqtt(net);
const byte DIR=25; char line[120];size_t pos=0;
unsigned long lastPoll=0,lastWifi=0,lastMqtt=0;int nextNode=1,waitingNode=0;
unsigned long sentAt=0;
struct Command {bool queued=false;String id;int pump=0,led=0;time_t expires=0;} jobs[3];
uint16_t crc(const char* p){uint16_t c=0xFFFF;while(*p){c^=(byte)*p++;for(byte i=0;i<8;i++)c=(c&1)?(c>>1)^0xA001:c>>1;}return c;}
void sendFrame(const char* body,int n){char out[125];snprintf(out,sizeof(out),"%s*%04X\n",body,crc(body));digitalWrite(DIR,HIGH);delayMicroseconds(100);Serial2.print(out);Serial2.flush();delayMicroseconds(100);digitalWrite(DIR,LOW);waitingNode=n;sentAt=millis();}
void incoming(char* topic,byte* payload,unsigned int length){if(length>256)return;int n=0;char expected[50];if(sscanf(topic,"smartfarm/v1/%d/command",&n)!=1||n<1||n>2)return;snprintf(expected,sizeof(expected),"smartfarm/v1/%d/command",n);if(strcmp(topic,expected))return;
 JsonDocument d;if(deserializeJson(d,payload,length))return;
 if(!d["id"].is<const char*>()||!d["pump"].is<int>()||!d["led"].is<int>()||!d["expires"].is<long>())return;
 String id=d["id"].as<String>();if(id.length()!=12)return;for(char c:id)if(!isxdigit(c))return;
 int p=d["pump"],l=d["led"];time_t now=time(nullptr),e=d["expires"].as<long>();if(now<1700000000||e<now||e>now+10||(p!=0&&p!=1)||l<0||l>3)return;
 jobs[n].id=id;jobs[n].pump=p;jobs[n].led=l;jobs[n].expires=e;jobs[n].queued=true;
}
void receive(){char* star=strchr(line,'*');if(!star||strlen(star+1)!=4)return;*star=0;if(crc(line)!=strtoul(star+1,NULL,16))return;
 int n,r,p,l;char id[17];if(sscanf(line,"S,%d,%16[^,],%d,%d,%d",&n,id,&r,&p,&l)!=5||n!=waitingNode)return;
 waitingNode=0;JsonDocument d;d["id"]=id;d["raw"]=r;d["pump"]=p;d["led"]=l;char json[150],topic[50];serializeJson(d,json,sizeof(json));snprintf(topic,sizeof(topic),"smartfarm/v1/%d/telemetry",n);mqtt.publish(topic,json,false);
}
void setup(){Serial.begin(115200);pinMode(DIR,OUTPUT);digitalWrite(DIR,LOW);Serial2.begin(9600,SERIAL_8N1,16,17);WiFi.begin(WIFI_SSID,WIFI_PASSWORD);configTime(0,0,"pool.ntp.org","time.google.com");mqtt.setServer(MQTT_HOST,1883);mqtt.setCallback(incoming);mqtt.setBufferSize(512);mqtt.setSocketTimeout(1);}
void loop(){unsigned long now=millis();if(WiFi.status()!=WL_CONNECTED){if(now-lastWifi>10000){lastWifi=now;WiFi.reconnect();}}else if(!mqtt.connected()&&now-lastMqtt>5000){lastMqtt=now;String id="farmgateway-"+String((uint32_t)ESP.getEfuseMac(),HEX);if(mqtt.connect(id.c_str(),MQTT_USER,MQTT_PASSWORD))mqtt.subscribe("smartfarm/v1/+/command",1);}
 mqtt.loop();while(Serial2.available()){char c=Serial2.read();if(c=='\n'){line[pos]=0;receive();pos=0;}else if(c!='\r'){if(pos<sizeof(line)-1)line[pos++]=c;else pos=0;}}
 if(waitingNode&&now-sentAt>180)waitingNode=0;
 if(!waitingNode&&now-lastPoll>=500){lastPoll=now;int n=nextNode;nextNode=3-nextNode;char body[90];if(jobs[n].queued&&time(nullptr)<=jobs[n].expires&&mqtt.connected()){snprintf(body,sizeof(body),"C,%d,%s,%d,%d",n,jobs[n].id.c_str(),jobs[n].pump,jobs[n].led);jobs[n].queued=false;}else{jobs[n].queued=false;snprintf(body,sizeof(body),"Q,%d",n);}sendFrame(body,n);}
}
