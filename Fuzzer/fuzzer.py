import paho.mqtt.client as mqtt
from paho.mqtt import publish
from config import *
from db.opdata import opmessage,opvulmessage
from db.optmp import optask
import logging,json
from mutator import JsonMutator
from time import sleep
from logger import logger
import argparse,os


# MQTT Publish
def mqtt_publish(topic,payload):
    logging.debug("topic:"+topic+"   payload:"+payload)
    if IS_TLS:
        publish.single(topic, payload, 
        hostname = IP,
        port = PORT,
        client_id =  CLIENT_ID,
        tls = TLS_CONFIG
        )
    else:
        publish.single(topic, payload, 
        hostname = IP,
        port = PORT,
        client_id =  CLIENT_ID
        )


# whether it is in json format
def is_json(json_str):
    try:
        json.loads(json_str)
    except ValueError:
        return False
    return True

# Generate test data.
def get_testing(topic,payload):
    message_mutation_list =[]
    if is_json(payload):
        message_mutation_list = get_json_mutation(topic,payload)
        #Save to database.
        db = optask()
        db.add_task(message_mutation_list)       
        logging.info("Add Task ")


# Generate payload of JSON.
def get_json_mutation(topic,payload):
    mutator =  JsonMutator(PAYLOAD_MODEL)
    message_mutation_list=[]
    mutation_list =mutator.get_paylaod_list(payload)
    for m in  mutation_list:
         message_mutation_list.append((topic,m))
    return message_mutation_list
    

# Deduplication
def deduplication(message_list):
    tmp_list =[]
    for mess in message_list:
        if mess not in tmp_list:
            topic,payload = mess
            tmp_list.append(mess)
    return tmp_list


# Mutation
def mutator():
    # First, clear the table of tmp task.
    db_tmp = optask()
    db_tmp.empty()
    logging.info("Mutator Start.")
    db = opmessage(DB_PATH)
    messages = db.query_message()
    messages = deduplication(messages)
    topic_tmp = []
    for (topic,payload) in messages:
        get_testing(topic,payload)
   
    logging.info("Target: "+BASE_PATH +" Seed: "+str( db.count())+" Fuzzing Payload: "+str(db_tmp.count()))
    logging.info("Mutator End.")



def fuzzer(start_id=0):
    logging.info("Fuzzer Start.")
    #init
    current_id = 0
    db_vul = opvulmessage(DB_PATH)
    db_vul.empty()
    db_tmp = optask()
    tasks = db_tmp.get_task(start_id)
    if not len(tasks):
        logging.error("No Task.")
        logging.info("Fuzzer End.")
        return 
    logging.info("Get Tasks "+ str(len(tasks)))
    db = opvulmessage(DB_PATH)
    vul_time = 0
    log = logger(LOGGER_PATH)
    for task in tasks:
        current_id = task[0]
        logging.info("Task "+str(current_id))
        mqtt_publish(task[1],task[2])
        #wait 
        sleep(WAIT_TIME)
        #Detect crash.
        result = db.check_vul()
        if len(result) !=0 and vul_time!= result[0][0]:
            result_time,vul_type,need_stop = result[0]
            vul_time = result_time
            logging.info("Find "+VUL_TYPE[vul_type]+ "_Vul! "+" topic:"+task[1]+" payload:"+task[2])
            #Save as a separate file.
            log.write("Find "+VUL_TYPE[vul_type]+ "_Vul! "+" topic:"+task[1]+" payload:"+task[2])
            if need_stop:
                logging.info("Stop.")
                logging.info("Fuzzer End.")
                return
    logging.info("Fuzzer End.")

def clear():
    db_tmp = optask()
    db_tmp.empty()
    db = opmessage(DB_PATH)
    db.empty()
    db2 = opvulmessage(DB_PATH)
    db2.empty()

def main():
    if not os.path.exists("data"):
        os.makedirs("data")
    parser = argparse.ArgumentParser()

    parser.add_argument("-m",'--mutate',dest = "m",action="store_true", help = "Mutate parameter.")
    parser.add_argument("-c",'--clear',dest = "c", help = "Clear tables of message , tmp and vulmessage. ")
    parser.add_argument("-f",'--fuzz',dest = "f", help = "Start fuzzer from task_id.")
    args = parser.parse_args()
    if args.m:
        mutator()
    if args.f:
        fuzzer(args.f)
    if args.c:
        clear()

if __name__ == "__main__":
    #mutator()
    #fuzzer()
    main()
  







