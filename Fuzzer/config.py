import logging
import os

#Broker连接配置
IP = '192.168.1.1'
PORT = 1883
IS_TLS = False
WAIT_TIME = 1
#{‘ca_certs’:”<ca_certs>”, ‘certfile’:”<certfile>”, ‘keyfile’:”<keyfile>”, ‘tls_version’:”<tls_version>”, ‘ciphers’:”<ciphers”>}
TLS_CONFIG ={
    "ca_certs" : "/etc/mosquitto/certs/ca.crt"
}

BASE_PATH = "data/totolink/"
if not os.path.exists(BASE_PATH):
    os.makedirs(BASE_PATH)
DB_PATH = BASE_PATH + "data.db"
LOGGER_PATH = BASE_PATH + "vul.log"
TMP_PATH = BASE_PATH + "tmp.db"
FILTER_PATH = BASE_PATH + "filter"
DEFAULT_COMMAND = "ping -c 1 " + IP 
DEFAULT_WRITE_FILE ="/tmp/re.about"
CLIENT_ID = "xulaoniubi"
# default,simple(payload精简集，更适合IoT),boofuzz
PAYLOAD_MODEL = "simple"
# 不进行变异的KEY
FILTER_LIST = ["topicurl"]


VUL_TYPE={
    1:"DoS",
    2:"CI",
}

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s',level=logging.INFO)
