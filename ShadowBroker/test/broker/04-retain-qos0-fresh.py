#!/usr/bin/env python3

# Test whether a retained PUBLISH to a topic with QoS 0 is sent with
# retain=false to an already subscribed client.

from mosq_test_helper import *

rc = 1
keepalive = 60
mid = 16
connect_packet = mosq_test.gen_connect("retain-qos0-fresh-test", keepalive=keepalive)
connack_packet = mosq_test.gen_connack(rc=0)

publish_packet = mosq_test.gen_publish("retain/qos0/test", qos=0, payload="retained message", retain=True)
publish_fresh_packet = mosq_test.gen_publish("retain/qos0/test", qos=0, payload="retained message")
subscribe_packet = mosq_test.gen_subscribe(mid, "retain/qos0/test", 0)
suback_packet = mosq_test.gen_suback(mid, 0)

port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    sock = mosq_test.do_client_connect(connect_packet, connack_packet, port=port)
    mosq_test.do_send_receive(sock, subscribe_packet, suback_packet, "suback")
    mosq_test.do_send_receive(sock, publish_packet, publish_fresh_packet, "publish")

    rc = 0

    sock.close()
finally:
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))

exit(rc)

