#!/usr/bin/env python3

# Test whether a client subscribed to a topic does not receive its own message
# sent to that topic if no local is set.
# MQTT v5

from mosq_test_helper import *

rc = 1
keepalive = 60
connect_packet = mosq_test.gen_connect("subpub-qos1-test", keepalive=keepalive, proto_ver=5)
connack_packet = mosq_test.gen_connack(rc=0, proto_ver=5)

mid = 530
subscribe_packet = mosq_test.gen_subscribe(mid, "subpub/qos1", 1 | mqtt5_opts.MQTT_SUB_OPT_NO_LOCAL, proto_ver=5)
suback_packet = mosq_test.gen_suback(mid, 1, proto_ver=5)

mid = 531
subscribe2_packet = mosq_test.gen_subscribe(mid, "subpub/receive", 1, proto_ver=5)
suback2_packet = mosq_test.gen_suback(mid, 1, proto_ver=5)

mid = 300
publish_packet = mosq_test.gen_publish("subpub/qos1", qos=1, mid=mid, payload="message", proto_ver=5)
puback_packet = mosq_test.gen_puback(mid, proto_ver=5)

mid = 301
publish2_packet = mosq_test.gen_publish("subpub/receive", qos=1, mid=mid, payload="success", proto_ver=5)
puback2_packet = mosq_test.gen_puback(mid, proto_ver=5)

mid = 1
publish3_packet = mosq_test.gen_publish("subpub/receive", qos=1, mid=mid, payload="success", proto_ver=5)


port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    sock = mosq_test.do_client_connect(connect_packet, connack_packet, timeout=20, port=port)

    mosq_test.do_send_receive(sock, subscribe_packet, suback_packet, "suback")
    mosq_test.do_send_receive(sock, subscribe2_packet, suback2_packet, "suback2")

    mosq_test.do_send_receive(sock, publish_packet, puback_packet, "puback")
    mosq_test.do_send_receive(sock, publish2_packet, puback2_packet, "puback2")

    if mosq_test.expect_packet(sock, "publish3", publish3_packet):
        rc = 0

    sock.close()
finally:
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))

exit(rc)

