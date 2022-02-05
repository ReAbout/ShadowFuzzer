#!/usr/bin/env python3

# Test whether a PUBLISH to a topic with QoS 2 results in the correct packet
# flow. This test introduces delays into the flow in order to force the broker
# to send duplicate PUBREC and PUBCOMP messages.

from mosq_test_helper import *

rc = 1
keepalive = 600
connect_packet = mosq_test.gen_connect("pub-qos2-timeout-test", keepalive=keepalive)
connack_packet = mosq_test.gen_connack(rc=0)

mid = 1926
publish_packet = mosq_test.gen_publish("pub/qos2/test", qos=2, mid=mid, payload="timeout-message")
pubrec_packet = mosq_test.gen_pubrec(mid)
pubrel_packet = mosq_test.gen_pubrel(mid)
pubcomp_packet = mosq_test.gen_pubcomp(mid)

broker = mosq_test.start_broker(filename=os.path.basename(__file__))

try:
    sock = mosq_test.do_client_connect(connect_packet, connack_packet)
    mosq_test.do_send_receive(sock, publish_packet, pubrec_packet, "pubrec")

    # Timeout is 8 seconds which means the broker should repeat the PUBREC.

    if mosq_test.expect_packet(sock, "pubrec", pubrec_packet):
        mosq_test.do_send_receive(sock, pubrel_packet, pubcomp_packet, "pubcomp")

        rc = 0

    sock.close()
finally:
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))

exit(rc)

