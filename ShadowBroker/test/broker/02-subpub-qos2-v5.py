#!/usr/bin/env python3

# Test whether a client subscribed to a topic receives its own message sent to that topic.
# MQTT v5

from mosq_test_helper import *

rc = 1
mid = 530
keepalive = 60
connect_packet = mosq_test.gen_connect("subpub-qos2-test", keepalive=keepalive, proto_ver=5)
connack_packet = mosq_test.gen_connack(rc=0, proto_ver=5)

subscribe_packet = mosq_test.gen_subscribe(mid, "subpub/qos2", 2, proto_ver=5)
suback_packet = mosq_test.gen_suback(mid, 2, proto_ver=5)

mid = 301
publish_packet = mosq_test.gen_publish("subpub/qos2", qos=2, mid=mid, payload="message", proto_ver=5)
pubrec_packet = mosq_test.gen_pubrec(mid, proto_ver=5)
pubrel_packet = mosq_test.gen_pubrel(mid, proto_ver=5)
pubcomp_packet = mosq_test.gen_pubcomp(mid, proto_ver=5)

mid = 1
publish_packet2 = mosq_test.gen_publish("subpub/qos2", qos=2, mid=mid, payload="message", proto_ver=5)
pubrec_packet2 = mosq_test.gen_pubrec(mid, proto_ver=5)
pubrel_packet2 = mosq_test.gen_pubrel(mid, proto_ver=5)
pubcomp_packet2 = mosq_test.gen_pubcomp(mid, proto_ver=5)


port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    sock = mosq_test.do_client_connect(connect_packet, connack_packet, timeout=20, port=port)

    mosq_test.do_send_receive(sock, subscribe_packet, suback_packet, "suback")
    mosq_test.do_send_receive(sock, publish_packet, pubrec_packet, "pubrec")
    mosq_test.do_send_receive(sock, pubrel_packet, pubcomp_packet, "pubcomp")

    if mosq_test.expect_packet(sock, "publish2", publish_packet2):
        mosq_test.do_send_receive(sock, pubrec_packet2, pubrel_packet2, "pubrel2")
        # Broker side of flow complete so can quit here.
        rc = 0

    sock.close()
finally:
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))

exit(rc)

