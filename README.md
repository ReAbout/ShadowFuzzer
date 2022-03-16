# ShadowFuzzer


The ShadowFuzzer is a fuzzing framework to find client-side vulnerabilities when processing incoming MQTT messages. 

## Attack Model

The attack targets are the IoT devices communicating with the MQTT broker. The adversary aims to leverage the broker as a trampoline to transfer
exploit messages to the target devices to trigger the vulnerabilities when processing the MQTT payload.

![](./doc/img/attack.png)

## Overview of ShadowFuzzer


![](./doc/img/fuzzing.png)

## How to use?

