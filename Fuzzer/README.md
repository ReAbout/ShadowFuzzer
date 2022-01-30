# The Fuzzer of ShadowFuzzer



## How to Use ?

#### Message Recoreder

```
python3 message_recoreder.py -i 192.168.0.1 -p 1883    
```

#### Fuzzing

1. Modify the configuration information of `config.py` according to the broker information.      
2. Mutate Data. Take samples from the data database (`DB_PATH = "data/data.db"`) for mutation and save to `tmp.db`.  
```
python3 mqttfuzzer.py -m 
```
3. Start the ShadowBroker.
4. Start fuzz. Set the start `task_id`, and start it again after stopping.   
```
python3 mqttfuzzer.py -f 1
```

Supported mutation strategies: default,simple
The discovered vulnerability information is saved separately: `LOGGER_PATH = "data/vul.log"`   



## Description of Mutator
The payload of the MQTT protocol PUBLISH control packet is mutated.
Setps：  
1. Determine the data format of Paylaod (JSON，String，Binary)
2. The payload of JSON format mutation。Recursively identify the type of the value of each item (Int，Float，String，Array), and processed according to different mutation rules。    

Types of Vulnerabilities Detected：   
* Command injection (Parameter injection)  
* Buffer overflow   
* Null pointer   
* Other DoS Vulnerabilities