#!/usr/bin/env python3

# Does a persisted PUBLISH keep its properties?

from mosq_test_helper import *

def write_config(filename, port):
    with open(filename, 'w') as f:
        f.write("port %d\n" % (port))
        f.write("persistence true\n")
        f.write("persistence_file mosquitto-%d.db\n" % (port))

port = mosq_test.get_port()
conf_file = os.path.basename(__file__).replace('.py', '.conf')
write_config(conf_file, port)

rc = 1
keepalive = 60
connect_packet = mosq_test.gen_connect(
    "persistent-props-test", keepalive=keepalive, clean_session=True, proto_ver=5
)
connack_packet = mosq_test.gen_connack(rc=0, proto_ver=5)

mid = 1
props = mqtt5_props.gen_byte_prop(mqtt5_props.PROP_PAYLOAD_FORMAT_INDICATOR, 1)
props += mqtt5_props.gen_string_prop(mqtt5_props.PROP_CONTENT_TYPE, "plain/text")
props += mqtt5_props.gen_string_prop(mqtt5_props.PROP_RESPONSE_TOPIC, "/dev/null")
props += mqtt5_props.gen_string_prop(mqtt5_props.PROP_CORRELATION_DATA, "2357289375902345")
props += mqtt5_props.gen_string_pair_prop(mqtt5_props.PROP_USER_PROPERTY, "name", "value")
publish_packet = mosq_test.gen_publish("subpub/qos1", qos=1, mid=mid, payload="message", proto_ver=5, properties=props, retain=True)
puback_packet = mosq_test.gen_puback(mid, reason_code=mqtt5_rc.MQTT_RC_NO_MATCHING_SUBSCRIBERS, proto_ver=5)

publish2_packet = mosq_test.gen_publish("subpub/qos1", qos=0, payload="message", proto_ver=5, properties=props, retain=True)

mid = 1
subscribe_packet = mosq_test.gen_subscribe(mid, "subpub/qos1", 0, proto_ver=5)
suback_packet = mosq_test.gen_suback(mid, 0, proto_ver=5)

if os.path.exists('mosquitto-%d.db' % (port)):
    os.unlink('mosquitto-%d.db' % (port))

broker = mosq_test.start_broker(filename=os.path.basename(__file__), use_conf=True, port=port)

(stdo1, stde1) = ("", "")
try:
    sock = mosq_test.do_client_connect(connect_packet, connack_packet, timeout=20, port=port)
    mosq_test.do_send_receive(sock, publish_packet, puback_packet, "puback")
    mosq_test.do_send_receive(sock, subscribe_packet, suback_packet, "suback")

    if mosq_test.expect_packet(sock, "publish2", publish2_packet):

        broker.terminate()
        broker.wait()
        (stdo1, stde1) = broker.communicate()
        sock.close()
        broker = mosq_test.start_broker(filename=os.path.basename(__file__), use_conf=True, port=port)

        sock = mosq_test.do_client_connect(connect_packet, connack_packet, timeout=20, port=port)
        mosq_test.do_send_receive(sock, subscribe_packet, suback_packet, "suback")

        if mosq_test.expect_packet(sock, "publish2", publish2_packet):
            rc = 0

    sock.close()
finally:
    os.remove(conf_file)
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))
    if os.path.exists('mosquitto-%d.db' % (port)):
        os.unlink('mosquitto-%d.db' % (port))


exit(rc)

