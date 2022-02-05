#!/usr/bin/env python3

# Test whether a clean session client has a QoS 1 message queued for it.

from mosq_test_helper import *

rc = 1
keepalive = 60
connect_packet = mosq_test.gen_connect("test-helper", keepalive=keepalive)
connack_packet = mosq_test.gen_connack(rc=0)

mid = 128
publish_packet = mosq_test.gen_publish("qos1/clean_session/test", qos=1, mid=mid, payload="clean-session-message")
puback_packet = mosq_test.gen_puback(mid)

port = mosq_test.get_port()
sock = mosq_test.do_client_connect(connect_packet, connack_packet, port=port)
mosq_test.do_send_receive(sock, publish_packet, puback_packet, "puback")

rc = 0

sock.close()

exit(rc)

