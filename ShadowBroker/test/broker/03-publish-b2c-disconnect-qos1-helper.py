#!/usr/bin/env python3

from mosq_test_helper import *

port = mosq_test.get_port()

rc = 1
keepalive = 60
connect_packet = mosq_test.gen_connect("test-helper", keepalive=keepalive)
connack_packet = mosq_test.gen_connack(rc=0)

mid = 128
publish_packet = mosq_test.gen_publish("qos1/disconnect/test", qos=1, mid=mid, payload="disconnect-message")
puback_packet = mosq_test.gen_puback(mid)

sock = mosq_test.do_client_connect(connect_packet, connack_packet, connack_error="helper connack", port=port)

mosq_test.do_send_receive(sock, publish_packet, puback_packet, "helper puback")

rc = 0

sock.close()

exit(rc)

