#!/usr/bin/env python3

# Test switching between persistence and a clean session.
#
# Bug #874:
#
#
# mosquitto_sub -i sub -t 'topic' -v -p 29883 -q 1 -d -c
# ^C
# mosquitto_sub -i sub -t 'topic' -v -p 29883 -q 1 -d
# ^C
# 
# SUBSCRIBE to topic is no longer respected by mosquitto
# 
# run:
# 
# mosquitto_sub -i sub -t 'topic' -v -p 29883 -q 1 -d -c
# 
# and in a separate shell
# 
# mosquitto_pub -i pub -t topic -m 'hello' -p 29883 -q 1
# 
# sub does not receive the message

from mosq_test_helper import *

rc = 1
keepalive = 60
connect_packet_sub_persistent = mosq_test.gen_connect("flipflop-test", keepalive=keepalive, clean_session=False)
connect_packet_sub_clean = mosq_test.gen_connect("flipflop-test", keepalive=keepalive, clean_session=True)
connack_packet_sub = mosq_test.gen_connack(rc=0)

connect_packet_pub = mosq_test.gen_connect("flipflop-test-pub", keepalive=keepalive)
connack_packet_pub = mosq_test.gen_connack(rc=0)

mid=1
subscribe_packet = mosq_test.gen_subscribe(mid, "flipflop/test", 1)
suback_packet = mosq_test.gen_suback(mid, 1)

mid=1
publish_packet = mosq_test.gen_publish("flipflop/test", qos=1, mid=mid, payload="message")
puback_packet = mosq_test.gen_puback(mid)


port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    # mosquitto_sub -i sub -t 'topic' -q 1 -d -c
    sub_sock = mosq_test.do_client_connect(connect_packet_sub_persistent, connack_packet_sub, port=port)
    mosq_test.do_send_receive(sub_sock, subscribe_packet, suback_packet, "subscribe persistent 1")
    # And disconnect
    sub_sock.close()

    # mosquitto_sub -i sub -t 'topic' -q 1 -d
    sub_sock = mosq_test.do_client_connect(connect_packet_sub_clean, connack_packet_sub, port=port)
    mosq_test.do_send_receive(sub_sock, subscribe_packet, suback_packet, "subscribe clean")
    # And disconnect
    sub_sock.close()

    # mosquitto_sub -i sub -t 'topic' -v -q 1 -d -c
    sub_sock = mosq_test.do_client_connect(connect_packet_sub_persistent, connack_packet_sub, port=port)
    mosq_test.do_send_receive(sub_sock, subscribe_packet, suback_packet, "subscribe persistent 2")

    # and in a separate shell
    # 
    # mosquitto_pub -i pub -t topic -m 'hello' -p 29883 -q 1
    pub_sock = mosq_test.do_client_connect(connect_packet_pub, connack_packet_pub, port=port)
    mosq_test.do_send_receive(pub_sock, publish_packet, puback_packet, "publish")

    if mosq_test.expect_packet(sub_sock, "publish receive", publish_packet):
        rc = 0

    sub_sock.close()
finally:
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))

exit(rc)

