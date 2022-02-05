#!/usr/bin/env python3

# Test whether a retained PUBLISH to a topic with QoS 1 is retained.
# Subscription is made with QoS 0 so the retained message should also have QoS
# 0.

from mosq_test_helper import *

rc = 1
keepalive = 60
connect_packet = mosq_test.gen_connect("retain-qos1-test", keepalive=keepalive)
connack_packet = mosq_test.gen_connack(rc=0)

mid = 6
publish_packet = mosq_test.gen_publish("retain/qos1/test", qos=1, mid=mid, payload="retained message", retain=True)
puback_packet = mosq_test.gen_puback(mid)
mid = 18
subscribe_packet = mosq_test.gen_subscribe(mid, "retain/qos1/test", 0)
suback_packet = mosq_test.gen_suback(mid, 0)
publish0_packet = mosq_test.gen_publish("retain/qos1/test", qos=0, payload="retained message", retain=True)

port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    sock = mosq_test.do_client_connect(connect_packet, connack_packet, port=port)
    mosq_test.do_send_receive(sock, publish_packet, puback_packet, "puback")
    mosq_test.do_send_receive(sock, subscribe_packet, suback_packet, "suback")

    if mosq_test.expect_packet(sock, "publish0", publish0_packet):
        rc = 0

    sock.close()
finally:
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))

exit(rc)

