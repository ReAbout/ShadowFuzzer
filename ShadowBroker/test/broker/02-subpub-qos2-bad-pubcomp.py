#!/usr/bin/env python3

# Test what the broker does if receiving a PUBCOMP in response to a QoS 2 PUBLISH.

from mosq_test_helper import *

rc = 1
keepalive = 60

connect_packet = mosq_test.gen_connect("subpub-qos2-test", keepalive=keepalive)
connack_packet = mosq_test.gen_connack(rc=0)

mid = 1
subscribe_packet = mosq_test.gen_subscribe(mid, "subpub/qos2", 2)
suback_packet = mosq_test.gen_suback(mid, 2)

helper_connect = mosq_test.gen_connect("helper", keepalive=keepalive)
helper_connack = mosq_test.gen_connack(rc=0)

mid = 1
publish1s_packet = mosq_test.gen_publish("subpub/qos2", qos=2, mid=mid, payload="message")
pubrec1s_packet = mosq_test.gen_pubrec(mid)
pubrel1s_packet = mosq_test.gen_pubrel(mid)
pubcomp1s_packet = mosq_test.gen_pubcomp(mid)

mid = 1
publish1r_packet = mosq_test.gen_publish("subpub/qos2", qos=2, mid=mid, payload="message")
pubcomp1r_packet = mosq_test.gen_pubcomp(mid)

pingreq_packet = mosq_test.gen_pingreq()
pingresp_packet = mosq_test.gen_pingresp()

port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    sock = mosq_test.do_client_connect(connect_packet, connack_packet, timeout=20, port=port)
    mosq_test.do_send_receive(sock, subscribe_packet, suback_packet, "suback")

    helper = mosq_test.do_client_connect(helper_connect, helper_connack, timeout=20, port=port)
    mosq_test.do_send_receive(helper, publish1s_packet, pubrec1s_packet, "pubrec 1s")
    mosq_test.do_send_receive(helper, pubrel1s_packet, pubcomp1s_packet, "pubcomp 1s")
    helper.close()

    if mosq_test.expect_packet(sock, "publish 1r", publish1r_packet):
        sock.send(pubcomp1r_packet)
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

