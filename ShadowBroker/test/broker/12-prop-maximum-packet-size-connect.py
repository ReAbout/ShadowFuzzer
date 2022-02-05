#!/usr/bin/env python3

# Test whether setting maximum packet size to smaller than a CONNACK packet
# results in the CONNECT being rejected.
# MQTTv5

from mosq_test_helper import *

rc = 1

keepalive = 10
props = mqtt5_props.gen_uint32_prop(mqtt5_props.PROP_MAXIMUM_PACKET_SIZE, 2)
connect_packet = mosq_test.gen_connect("test", proto_ver=5, keepalive=keepalive, properties=props)

port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    sock = mosq_test.do_client_connect(connect_packet, b"", port=port)
    # Exception occurs if connack packet returned
    rc = 0
finally:
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))

exit(rc)

