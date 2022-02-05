#!/usr/bin/env python3

# Test whether a SUBSCRIBE to a topic with QoS 2 results in the correct SUBACK packet.
# MQTT 5

from mosq_test_helper import *

rc = 1
mid = 3
keepalive = 60
connect_packet = mosq_test.gen_connect("unsubscribe-qos2-test", keepalive=keepalive, proto_ver=5)
connack_packet = mosq_test.gen_connack(rc=0, proto_ver=5)

unsubscribe_packet = mosq_test.gen_unsubscribe(mid, "qos2/test", proto_ver=5)
unsuback_packet = mosq_test.gen_unsuback(mid, proto_ver=5, reason_code=17)

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

