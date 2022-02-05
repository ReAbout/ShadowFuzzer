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

