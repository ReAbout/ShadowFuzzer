#!/usr/bin/env python3

# Test whether a CONNECT with an invalid protocol number results in the correct CONNACK packet.

from mosq_test_helper import *

rc = 1
keepalive = 10
connect_packet = mosq_test.gen_connect("connect-invalid-test", keepalive=keepalive, proto_ver=0)
connack_packet = mosq_test.gen_connack(rc=1)

port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    sock = mosq_test.do_client_connect(connect_packet, connack_packet, port=port)
    sock.close()
    rc = 0

finally:
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))

exit(rc)

