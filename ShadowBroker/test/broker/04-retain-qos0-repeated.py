#!/usr/bin/env python3

# Test whether a retained PUBLISH to a topic with QoS 0 is actually retained
# and delivered when multiple sub/unsub operations are carried out.

from mosq_test_helper import *

rc = 1
keepalive = 60
mid = 16
connect_packet = mosq_test.gen_connect("retain-qos0-rep-test", keepalive=keepalive)
connack_packet = mosq_test.gen_connack(rc=0)

publish_packet = mosq_test.gen_publish("retain/qos0/test", qos=0, payload="retained message", retain=True)
subscribe_packet = mosq_test.gen_subscribe(mid, "retain/qos0/test", 0)
suback_packet = mosq_test.gen_suback(mid, 0)

unsub_mid = 13
unsubscribe_packet = mosq_test.gen_unsubscribe(unsub_mid, "retain/qos0/test")
unsuback_packet = mosq_test.gen_unsuback(unsub_mid)

port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    sock = mosq_test.do_client_connect(connect_packet, connack_packet, timeout=20, port=port)
    sock.send(publish_packet)
    mosq_test.do_send_receive(sock, subscribe_packet, suback_packet, "suback")

    if mosq_test.expect_packet(sock, "publish", publish_packet):
        mosq_test.do_send_receive(sock, unsubscribe_packet, unsuback_packet, "unsuback")
        mosq_test.do_send_receive(sock, subscribe_packet, suback_packet, "suback")

        if mosq_test.expect_packet(sock, "publish", publish_packet):
            rc = 0

    sock.close()
finally:
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))

exit(rc)

