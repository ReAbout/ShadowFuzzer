#!/usr/bin/env python3

from mosq_test_helper import *

port = mosq_test.get_port()

rc = 1
keepalive = 60
connect_packet = mosq_test.gen_connect("test-helper", keepalive=keepalive)
connack_packet = mosq_test.gen_connack(rc=0)

publish_packet = mosq_test.gen_publish("test", qos=0, payload="mount point")

sock = mosq_test.do_client_connect(connect_packet, connack_packet, port=port, connack_error="helper connack")
sock.send(publish_packet)
rc = 0
sock.close()

exit(rc)

