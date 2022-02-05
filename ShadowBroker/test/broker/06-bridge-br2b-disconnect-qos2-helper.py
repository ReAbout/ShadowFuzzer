#!/usr/bin/env python3

from mosq_test_helper import *

port = mosq_test.get_port()

rc = 1
keepalive = 60
connect_packet = mosq_test.gen_connect("test-helper", keepalive=keepalive)
connack_packet = mosq_test.gen_connack(rc=0)

mid = 312
publish_packet = mosq_test.gen_publish("bridge/disconnect/test", qos=2, mid=mid, payload="disconnect-message")
pubrec_packet = mosq_test.gen_pubrec(mid)
pubrel_packet = mosq_test.gen_pubrel(mid)
pubcomp_packet = mosq_test.gen_pubcomp(mid)

sock = mosq_test.do_client_connect(connect_packet, connack_packet, port=port, connack_error="helper connack")
sock.send(publish_packet)

if mosq_test.expect_packet(sock, "helper pubrec", pubrec_packet):
    sock.send(pubrel_packet)

    if mosq_test.expect_packet(sock, "helper pubcomp", pubcomp_packet):
        rc = 0

sock.close()

exit(rc)

