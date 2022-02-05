#!/usr/bin/env python3

# Test whether a duplicate CONNECT is rejected. MQTT v5

from mosq_test_helper import *

rc = 1
keepalive = 10
connect_packet = mosq_test.gen_connect("connect-test", keepalive=keepalive, proto_ver=5)
connack_packet = mosq_test.gen_connack(rc=0, proto_ver=5)

port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    sock = mosq_test.do_client_connect(connect_packet, connack_packet, port=port)
    sock.settimeout(3)
    sock.send(connect_packet)
    data = sock.recv(1)
    if len(data) == 0:
        rc = 0
except socket.error:
    rc = 0
finally:
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))

exit(rc)

