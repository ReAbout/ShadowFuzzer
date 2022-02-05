#!/usr/bin/env python3

# Test whether a PUBLISH to a topic with QoS 2 results in the correct packet flow.

from mosq_test_helper import *

rc = 1
keepalive = 60
connect_packet = mosq_test.gen_connect("test-helper", keepalive=keepalive)
connack_packet = mosq_test.gen_connack(rc=0)

mid = 312
publish_packet = mosq_test.gen_publish("qos2/timeout/test", qos=2, mid=mid, payload="timeout-message")
pubrec_packet = mosq_test.gen_pubrec(mid)
pubrel_packet = mosq_test.gen_pubrel(mid)
pubcomp_packet = mosq_test.gen_pubcomp(mid)

sock = mosq_test.do_client_connect(connect_packet, connack_packet, connack_error="helper connack")
mosq_test.do_send_receive(sock, publish_packet, pubrec_packet, "helper pubrec")
mosq_test.do_send_receive(sock, pubrel_packet, pubcomp_packet, "helper pubcomp")

rc = 0

sock.close()

exit(rc)

