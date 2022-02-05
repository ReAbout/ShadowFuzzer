#!/usr/bin/env python3

# Test whether a PUBREC with reason code >= 0x80 is handled correctly

from mosq_test_helper import *

rc = 1
keepalive = 60
connect_packet = mosq_test.gen_connect("pub-qo2-timeout-test", keepalive=keepalive, proto_ver=5)
connack_packet = mosq_test.gen_connack(rc=0, proto_ver=5)

mid = 1
subscribe_packet = mosq_test.gen_subscribe(mid, "qos2/pubrec/+", 2, proto_ver=5)
suback_packet = mosq_test.gen_suback(mid, 2, proto_ver=5)

mid = 1
publish_1_packet = mosq_test.gen_publish("qos2/pubrec/rejected", qos=2, mid=mid, payload="rejected-message", proto_ver=5)
pubrec_1_packet = mosq_test.gen_pubrec(mid, proto_ver=5, reason_code=0x80)

mid = 2
publish_2_packet = mosq_test.gen_publish("qos2/pubrec/accepted", qos=2, mid=mid, payload="accepted-message", proto_ver=5)
pubrec_2_packet = mosq_test.gen_pubrec(mid, proto_ver=5)
pubrel_2_packet = mosq_test.gen_pubrel(mid, proto_ver=5)
pubcomp_2_packet = mosq_test.gen_pubcomp(mid, proto_ver=5)

port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    sock = mosq_test.do_client_connect(connect_packet, connack_packet, port=port)
    mosq_test.do_send_receive(sock, subscribe_packet, suback_packet, "suback")
    pub = subprocess.Popen(['./02-subpub-qos2-pubrec-error-helper.py', str(port)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pub.wait()
    (stdo, stde) = pub.communicate()
    # Should have now received a publish command

    if mosq_test.expect_packet(sock, "publish 1", publish_1_packet):
        sock.send(pubrec_1_packet)

        if mosq_test.expect_packet(sock, "publish 2", publish_2_packet):
            mosq_test.do_send_receive(sock, pubrec_2_packet, pubrel_2_packet, "pubrel 2")
            sock.send(pubcomp_2_packet)
            rc = 0

    sock.close()
finally:
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))

exit(rc)

