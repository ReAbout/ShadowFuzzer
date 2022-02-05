#!/usr/bin/env python3

# Test whether a v5 UNSUBSCRIBE to multiple topics with QoS 2 results in the
# correct UNSUBACK packet, when one subscription exists and the other does not.

from mosq_test_helper import *

rc = 1
keepalive = 60
connect_packet = mosq_test.gen_connect("unsubscribe-qos2-test", keepalive=keepalive, proto_ver=5)
connack_packet = mosq_test.gen_connack(rc=0, proto_ver=5)

mid = 1
subscribe_packet = mosq_test.gen_subscribe(mid, "qos2/two", 2, proto_ver=5)
suback_packet = mosq_test.gen_suback(mid, 2, proto_ver=5)

mid = 3
unsubscribe_packet = mosq_test.gen_unsubscribe_multiple(mid, ["qos2/one", "qos2/two"], proto_ver=5)
unsuback_packet = mosq_test.gen_unsuback(mid, proto_ver=5, reason_code=[17, 0])

port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    sock = mosq_test.do_client_connect(connect_packet, connack_packet, port=port)
    mosq_test.do_send_receive(sock, subscribe_packet, suback_packet, "suback")
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

