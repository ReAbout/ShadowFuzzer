#!/usr/bin/env python3

# Test whether a UNSUBSCRIBE with no topic results in a disconnect. MQTT-3.10.3-2

from mosq_test_helper import *

def gen_unsubscribe_invalid_no_topic(mid):
    pack_format = "!BBH"
    return struct.pack(pack_format, 162, 2, mid)

rc = 1
mid = 3
keepalive = 60
connect_packet = mosq_test.gen_connect("unsubscribe-invalid-no-topic-test", keepalive=keepalive, proto_ver=4)
connack_packet = mosq_test.gen_connack(rc=0)

unsubscribe_packet = gen_unsubscribe_invalid_no_topic(mid)

port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    sock = mosq_test.do_client_connect(connect_packet, connack_packet, port=port)
    mosq_test.do_send_receive(sock, unsubscribe_packet, b"", "disconnect")

    rc = 0

    sock.close()
finally:
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))

exit(rc)

