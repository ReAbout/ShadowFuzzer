#!/usr/bin/env python3

# Test what the broker does if receiving a PUBREC in response to a QoS 1 PUBLISH.

from mosq_test_helper import *

rc = 1
keepalive = 60

connect_packet = mosq_test.gen_connect("subpub-qos1-test", keepalive=keepalive)
connack_packet = mosq_test.gen_connack(rc=0)

mid = 1
subscribe_packet = mosq_test.gen_subscribe(mid, "subpub/qos1", 1)
suback_packet = mosq_test.gen_suback(mid, 1)

helper_connect = mosq_test.gen_connect("helper", keepalive=keepalive)
helper_connack = mosq_test.gen_connack(rc=0)

mid = 1
publish1s_packet = mosq_test.gen_publish("subpub/qos1", qos=1, mid=mid, payload="message")
puback1s_packet = mosq_test.gen_puback(mid)

mid = 1
publish1r_packet = mosq_test.gen_publish("subpub/qos1", qos=1, mid=mid, payload="message")
pubrec1r_packet = mosq_test.gen_pubrec(mid)

pingreq_packet = mosq_test.gen_pingreq()
pingresp_packet = mosq_test.gen_pingresp()

port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    sock = mosq_test.do_client_connect(connect_packet, connack_packet, timeout=20, port=port)
    mosq_test.do_send_receive(sock, subscribe_packet, suback_packet, "suback")

    helper = mosq_test.do_client_connect(helper_connect, helper_connack, timeout=20, port=port)
    mosq_test.do_send_receive(helper, publish1s_packet, puback1s_packet, "puback 1s")
    helper.close()

    if mosq_test.expect_packet(sock, "publish 1r", publish1r_packet):
        sock.send(pubrec1r_packet)
        sock.send(pingreq_packet)
        p = sock.recv(len(pingresp_packet))
        if len(p) == 0:
            rc = 0

    sock.close()
except socket.error as e:
    if e.errno == errno.ECONNRESET:
        # Connection has been closed by peer, this is the expected behaviour
        rc = 0
finally:
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))

exit(rc)

