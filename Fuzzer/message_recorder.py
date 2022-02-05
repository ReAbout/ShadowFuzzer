from db.opdata import opmessage
import argparse
import logging
from config import DB_PATH,FILTER_PATH
import paho.mqtt.client as mqtt
import re,os

db = opmessage(DB_PATH)
tmp_list = []

def topic_filter(filename,topic):
    rules =[]

    with open(filename) as f:
        rules = f.readlines()
        for rule in rules :
            rule=rule.replace('\n', '').replace('\r', '')
            if re.match(rule,topic):
                
                return True
    return False


def on_connect(client, userdata, flags, rc):
    print("Message Recorder Start.")
    client.subscribe("#")

def on_message(client, userdata, msg):
    if FILTER_PATH and os.path.exists(FILTER_PATH):
        if topic_filter(FILTER_PATH,msg.topic):
            return
    if (msg.topic,msg.payload) not in tmp_list:
        logging.info(msg.topic+" , "+str(msg.payload))
        tmp_list.append((msg.topic,msg.payload))
        db.add_message([(msg.topic,msg.payload,"",1)])

    

def mqtt_sub(ip,port):
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(ip, port, 60)
    client.loop_forever()



def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("-i",'--ip',dest = "i", help = "MQTT Server IP.")
    parser.add_argument("-p",'--port',dest = "p", help = "MQTT Server Port.")
    #parser.add_argument("-f",'--filter',dest = "f", help = "Rules of Filter Topic.")
    args = parser.parse_args()
    if args.i and args.p:
        mqtt_sub(args.i,int(args.p))
    '''
    global filename
    filename =""
    if args.f:
        
        filename = args.f
    '''


if __name__ == "__main__":
    main()
    
