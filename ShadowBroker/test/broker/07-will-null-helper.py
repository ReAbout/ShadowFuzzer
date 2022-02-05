#!/usr/bin/env python3

# Connect a client with a will, then disconnect without DISCONNECT.

from mosq_test_helper import *

rc = 1
keepalive = 60
connect_packet = mosq_test.gen_connect("test-helper", keepalive=keepalive, will_topic="will/null/test")
connack_packet = mosq_test.gen_connack(rc=0)

port = mosq_test.get_port()
sock = mosq_test.do_client_connect(connect_packet, connack_packet, port=port)
rc = 0
sock.close()

exit(rc)

