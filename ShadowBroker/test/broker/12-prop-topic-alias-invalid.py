#!/usr/bin/env python3

# Test whether the broker handles a topic alias of >max_topic_alias correctly.
# MQTTv5

from mosq_test_helper import *

def do_test(value):
    rc = 1

    keepalive = 10
    connect_packet = mosq_test.gen_connect("test", proto_ver=5, keepalive=keepalive)
    connack_packet = mosq_test.gen_connack(rc=0, proto_ver=5)

    props = mqtt5_props.gen_uint16_prop(mqtt5_props.PROP_TOPIC_ALIAS, value)
    publish_packet = mosq_test.gen_publish(topic="test/topic", qos=0, payload="12345678901234567890", proto_ver=5, properties=props)

    disconnect_packet = mosq_test.gen_disconnect(reason_code=mqtt5_rc.MQTT_RC_TOPIC_ALIAS_INVALID, proto_ver=5)
    port = mosq_test.get_port()
    broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

    try:
        sock = mosq_test.do_client_connect(connect_packet, connack_packet, port=port)
        sock.send(publish_packet)
        if mosq_test.expect_packet(sock, "disconnect", disconnect_packet):
            rc = 0
    finally:
        broker.terminate()
        broker.wait()
        (stdo, stde) = broker.communicate()
        if rc:
            print(stde.decode('utf-8'))
            exit(rc)


do_test(11)

