#!/usr/bin/env python3

from mosq_test_helper import *

rc = 1
mid = 3265
keepalive = 60
connect_packet = mosq_test.gen_connect("pub-qos2-disco-test", keepalive=keepalive, clean_session=False, proto_ver=3)
connack_packet = mosq_test.gen_connack(flags=0, rc=0)

subscribe_packet = mosq_test.gen_subscribe(mid, "qos2/disconnect/test", 2)
suback_packet = mosq_test.gen_suback(mid, 2)

mid = 1
publish_packet = mosq_test.gen_publish("qos2/disconnect/test", qos=2, mid=mid, payload="disconnect-message")
publish_dup_packet = mosq_test.gen_publish("qos2/disconnect/test", qos=2, mid=mid, payload="disconnect-message", dup=True)
pubrec_packet = mosq_test.gen_pubrec(mid)
pubrel_packet = mosq_test.gen_pubrel(mid)
pubrel_dup_packet = mosq_test.gen_pubrel(mid, dup=True)
pubcomp_packet = mosq_test.gen_pubcomp(mid)

port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    sock = mosq_test.do_client_connect(connect_packet, connack_packet, port=port)

    mosq_test.do_send_receive(sock, publish_packet, pubrec_packet, "pubrec")

    # We're now going to disconnect and pretend we didn't receive the pubrec.
    sock.close()

    sock = mosq_test.do_client_connect(connect_packet, connack_packet, port=port)
    sock.send(publish_dup_packet)

    if mosq_test.expect_packet(sock, "pubrec", pubrec_packet):
        mosq_test.do_send_receive(sock, pubrel_packet, pubcomp_packet, "pubcomp")

        # Again, pretend we didn't receive this pubcomp
        sock.close()

        sock = mosq_test.do_client_connect(connect_packet, connack_packet, port=port)
        mosq_test.do_send_receive(sock, pubrel_dup_packet, pubcomp_packet, "pubcomp")

        rc = 0

        sock.close()
finally:
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))

exit(rc)

