#!/usr/bin/env python3

# Test whether a SUBSCRIBE to a topic with QoS 1 results in the correct SUBACK packet.

from mosq_test_helper import *

rc = 1
mid = 79
keepalive = 60
connect_packet = mosq_test.gen_connect("subscribe-qos1-test", keepalive=keepalive)
connack_packet = mosq_test.gen_connack(rc=0)

subscribe_packet = mosq_test.gen_subscribe(mid, "qos1/test", 1)
suback_packet = mosq_test.gen_suback(mid, 1)

port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    sock = mosq_test.do_client_connect(connect_packet, connack_packet, port=port)
    mosq_test.do_send_receive(sock, subscribe_packet, suback_packet, "suback")

    rc = 0

    sock.close()
finally:
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))

exit(rc)

