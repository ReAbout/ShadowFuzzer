#!/usr/bin/env python3

# Test whether sending a non zero session expiry interval in DISCONNECT after
# having sent a zero session expiry interval is treated correctly in MQTT v5.

from mosq_test_helper import *

rc = 1

keepalive = 10
props = mqtt5_props.gen_uint32_prop(mqtt5_props.PROP_SESSION_EXPIRY_INTERVAL, 0)
connect_packet = mosq_test.gen_connect("test", proto_ver=5, keepalive=keepalive, properties=props)

connack_packet = mosq_test.gen_connack(rc=0, proto_ver=5)

props = mqtt5_props.gen_uint32_prop(mqtt5_props.PROP_SESSION_EXPIRY_INTERVAL, 1)
disconnect_client_packet = mosq_test.gen_disconnect(proto_ver=5, properties=props)

disconnect_server_packet = mosq_test.gen_disconnect(proto_ver=5, reason_code=130)

port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    sock = mosq_test.do_client_connect(connect_packet, connack_packet, port=port)
    mosq_test.do_send_receive(sock, disconnect_client_packet, disconnect_server_packet, "disconnect")
    sock.close()
    rc = 0
finally:
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))

exit(rc)

