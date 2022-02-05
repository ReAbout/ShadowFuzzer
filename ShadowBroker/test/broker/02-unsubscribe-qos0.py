#!/usr/bin/env python3

# Test whether a UNSUBSCRIBE to a topic with QoS 0 results in the correct UNSUBACK packet.
# This doesn't assume a subscription exists.

from mosq_test_helper import *

rc = 1
mid = 53
keepalive = 60
connect_packet = mosq_test.gen_connect("unsubscribe-qos0-test", keepalive=keepalive)
connack_packet = mosq_test.gen_connack(rc=0)

unsubscribe_packet = mosq_test.gen_unsubscribe(mid, "qos0/test")
unsuback_packet = mosq_test.gen_unsuback(mid)

port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    sock = mosq_test.do_client_connect(connect_packet, connack_packet, port=port)
    mosq_test.do_send_receive(sock, unsubscribe_packet, unsuback_packet, "unsuback")

    rc = 0

    sock.close()
finally:
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))

exit(rc)

