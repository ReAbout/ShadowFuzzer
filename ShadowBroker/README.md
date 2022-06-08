# Shadow Broker

Shadow broker building with mosquitto.

# Dependencies

## CentOS 7

yum install -y openssl-devel c-ares-devel libuuid-devel cmake libssl-dev libc-ares-dev uuid-dev

# Compile

## With Fuzzer

cd ./src  
make

## Without Fuzzer
vim config.mk,
set WITH_FUZZER to no  

## Configuration

The configuration file is /etc/mosquitto/mosquitto.conf. In addition to mosquitto parameters, the following parameters need to be added:

* fuzz_db_file: The location of the sqlite3 database, which contains message information and vulnerability information. The test case messages are in message table, and the messages that trigger the vuls are in vulmessage table.

* fuzz_avoid_clientid: The client ID from which the ShadowBroker doesn't record messages. Before fuzzing starts, this parameter should be the fuzzer's client ID.

* fuzz_ping_from_ip: Due to that we use a injection of a "ping" command to trigger the command injection vulnerabilities, the device will send an ICMP echo request packet to the ShadowBroker when a vulnerability triggered. Therefore, this parameter should be the source of the ICMP packet, i.e. the IP address of the target device.


* fuzz_client_ip: The IP address of the subscriber.

## Use

* Make the target to connect to the ShadowBroker first.
* Make the publisher to connect to the ShadowBroker and publish messages, the ShadowBroker can record these messages into the database as seeds. Or you can collect the messages from the real-world broker and import them to the database manually.
* Boot the fuzzer. The vulnerabililies are recorded in the vulmessage table of the database. The fuzzer watch this table continuously, once a vulnerable message occurs, the fuzzer print the information in console.