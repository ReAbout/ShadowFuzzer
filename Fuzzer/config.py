import logging
import os

#Broker configuration
IP = '192.168.1.1'
PORT = 1883
IS_TLS = False
WAIT_TIME = 1
#{'ca_certs':'<ca_certs>', 'certfile':'<certfile>', 'keyfile':'<keyfile>', 'tls_version':'<tls_version>', 'ciphers':'<ciphers'>}
TLS_CONFIG ={
    "ca_certs" : "/etc/mosquitto/certs/ca.crt"
}

BASE_PATH = "data/totolink/"
if not os.path.exists(BASE_PATH):
    os.makedirs(BASE_PATH)
DB_PATH = BASE_PATH + "data.db"
LOGGER_PATH = BASE_PATH + "vul.log"
TMP_PATH = BASE_PATH + "tmp.db"
#Filter file path used by the message recorder.
FILTER_PATH = BASE_PATH + "filter"
DEFAULT_COMMAND = "ping -c 1 " + IP 
DEFAULT_WRITE_FILE ="/tmp/re.about"
CLIENT_ID = "xulaoniubi"
# default,simple(A simple collection of payloads, more suitable for IoT)
PAYLOAD_MODEL = "simple"
# The key without mutation.
FILTER_LIST = ["topicurl"]


VUL_TYPE={
    1:"DoS",
    2:"CI",
}

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s',level=logging.INFO)
