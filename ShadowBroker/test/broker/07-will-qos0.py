#!/usr/bin/env python3

# Test whether a client will is transmitted correctly.

from mosq_test_helper import *


def do_test(proto_ver, clean_session):
    rc = 1
    mid = 53
    keepalive = 60
    connect1_packet = mosq_test.gen_connect("will-qos0-test", keepalive=keepalive, proto_ver=proto_ver)
    connack1_packet = mosq_test.gen_connack(rc=0, proto_ver=proto_ver)

    if proto_ver == 5:
        props = mqtt5_props.gen_uint32_prop(mqtt5_props.PROP_SESSION_EXPIRY_INTERVAL, 100)
    else:
        props = None

    connect2_packet = mosq_test.gen_connect("test-helper", keepalive=keepalive, will_topic="will/qos0/test", will_payload=b"will-message", clean_session=clean_session, proto_ver=proto_ver, properties=props)
    connack2_packet = mosq_test.gen_connack(rc=0, proto_ver=proto_ver)

    subscribe_packet = mosq_test.gen_subscribe(mid, "will/qos0/test", 0, proto_ver=proto_ver)
    suback_packet = mosq_test.gen_suback(mid, 0, proto_ver=proto_ver)

    publish_packet = mosq_test.gen_publish("will/qos0/test", qos=0, payload="will-message", proto_ver=proto_ver)

    port = mosq_test.get_port()
    broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

    try:
        sock = mosq_test.do_client_connect(connect1_packet, connack1_packet, timeout=5, port=port)
        mosq_test.do_send_receive(sock, subscribe_packet, suback_packet, "suback")

        sock2 = mosq_test.do_client_connect(connect2_packet, connack2_packet, port=port, timeout=5)
        sock2.close()

        if mosq_test.expect_packet(sock, "publish", publish_packet):
            rc = 0

        sock.close()
    except Exception as e:
        print(e)
    finally:
        broker.terminate()
        broker.wait()
        (stdo, stde) = broker.communicate()
        if rc:
            print(stde.decode('utf-8'))
            exit(rc)

do_test(4, True)
do_test(4, False)
do_test(5, True)
do_test(5, False)
exit(0)

