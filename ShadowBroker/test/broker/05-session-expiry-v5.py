#!/usr/bin/env python3

# MQTT v5. Test whether session expiry interval works correctly.

from mosq_test_helper import *

rc = 1
keepalive = 60

props = mqtt5_props.gen_uint32_prop(mqtt5_props.PROP_SESSION_EXPIRY_INTERVAL, 1)
connect_packet = mosq_test.gen_connect("clean-qos2-test", keepalive=keepalive, clean_session=False, proto_ver=5, properties=props)
connack1_packet = mosq_test.gen_connack(flags=0, rc=0, proto_ver=5)

connack2_packet = mosq_test.gen_connack(flags=1, rc=0, proto_ver=5)

props = mqtt5_props.gen_uint32_prop(mqtt5_props.PROP_SESSION_EXPIRY_INTERVAL, 3)
disconnect_packet = mosq_test.gen_disconnect(proto_ver=5, properties=props)

props = mqtt5_props.gen_uint32_prop(mqtt5_props.PROP_SESSION_EXPIRY_INTERVAL, 0)
disconnect2_packet = mosq_test.gen_disconnect(proto_ver=5, properties=props)

port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    # First connect, clean start is false, we expect a normal connack
    sock = mosq_test.do_client_connect(connect_packet, connack1_packet, port=port, connack_error="connack 1")
    # Forceful disconnect
    sock.close()

    # Immediate second connect, clean start is false, we expect a connack with
    # previous state
    sock = mosq_test.do_client_connect(connect_packet, connack2_packet, port=port, connack_error="connack 2")
    sock.close()

    # Session should expire in one second, so sleep longer
    time.sleep(2)

    # Third connect, clean start is false, session should have expired so we
    # expect a normal connack
    sock = mosq_test.do_client_connect(connect_packet, connack1_packet, port=port, connack_error="connack 3")
    # Send DISCONNECT with new session expiry, then close
    sock.send(disconnect_packet)
    sock.close()

    # Immediate reconnect, clean start is false, we expect a connack with
    # previous state
    sock = mosq_test.do_client_connect(connect_packet, connack2_packet, port=port, connack_error="connack 4")
    # Send DISCONNECT with new session expiry, then close
    sock.send(disconnect_packet)
    sock.close()

    # Session should expire in three seconds if it has been updated, sleep for
    # 2 to check it is updated from 1 second.
    time.sleep(2)

    # Immediate reconnect, clean start is false, we expect a connack with
    # previous state
    sock = mosq_test.do_client_connect(connect_packet, connack2_packet, port=port, connack_error="connack 5")
    # Send DISCONNECT with new session expiry, then close
    sock.send(disconnect_packet)
    sock.close()

    # Session should expire in three seconds, so sleep longer
    time.sleep(4)
    # Third connect, clean start is false, session should have expired so we
    # expect a normal connack
    sock = mosq_test.do_client_connect(connect_packet, connack1_packet, port=port, connack_error="connack 6")
    # Send DISCONNECT with 0 session expiry, then close
    sock.send(disconnect2_packet)
    sock.close()

    # Immediate reconnect, session should have been removed.
    sock = mosq_test.do_client_connect(connect_packet, connack1_packet, port=port, connack_error="connack 7")
    sock.close()
    rc = 0

    sock.close()
finally:
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))

exit(rc)

