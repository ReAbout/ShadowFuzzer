#!/usr/bin/env python3

from mosq_test_helper import *

rc = 1
keepalive = 60
connect_packet = mosq_test.gen_connect("test-helper", keepalive=keepalive)
connack_packet = mosq_test.gen_connack(rc=0)

mid = 1
publish_1_packet = mosq_test.gen_publish("qos2/pubrec/rejected", qos=2, mid=mid, payload="rejected-message")
pubrec_1_packet = mosq_test.gen_pubrec(mid)
pubrel_1_packet = mosq_test.gen_pubrel(mid)
pubcomp_1_packet = mosq_test.gen_pubcomp(mid)

mid = 2
publish_2_packet = mosq_test.gen_publish("qos2/pubrec/accepted", qos=2, mid=mid, payload="accepted-message")
pubrec_2_packet = mosq_test.gen_pubrec(mid)
pubrel_2_packet = mosq_test.gen_pubrel(mid)
pubcomp_2_packet = mosq_test.gen_pubcomp(mid)

port = mosq_test.get_port()
sock = mosq_test.do_client_connect(connect_packet, connack_packet, connack_error="helper connack", port=port)

mosq_test.do_send_receive(sock, publish_1_packet, pubrec_1_packet, "helper pubrec")
mosq_test.do_send_receive(sock, pubrel_1_packet, pubcomp_1_packet, "helper pubcomp")

mosq_test.do_send_receive(sock, publish_2_packet, pubrec_2_packet, "helper pubrec")
mosq_test.do_send_receive(sock, pubrel_2_packet, pubcomp_2_packet, "helper pubcomp")

rc = 0

sock.close()

exit(rc)

