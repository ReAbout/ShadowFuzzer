#!/usr/bin/env python3

# Test whether the broker reduces the message expiry interval when republishing.
# MQTT v5

# Client connects with clean session set false, subscribes with qos=1, then disconnects
# Helper publishes two messages, one with a short expiry and one with a long expiry
# We wait until the short expiry will have expired but the long one not.
# Client reconnects, expects delivery of the long expiry message with a reduced
# expiry interval property.

from mosq_test_helper import *

rc = 1
mid = 53
keepalive = 60
props = mqtt5_props.gen_uint32_prop(mqtt5_props.PROP_SESSION_EXPIRY_INTERVAL, 60)
connect_packet = mosq_test.gen_connect("subpub-qos0-test", keepalive=keepalive, proto_ver=5, clean_session=False, properties=props)
connack1_packet = mosq_test.gen_connack(rc=0, proto_ver=5)
connack2_packet = mosq_test.gen_connack(rc=0, proto_ver=5, flags=1)

subscribe_packet = mosq_test.gen_subscribe(mid, "subpub/qos1", 1, proto_ver=5)
suback_packet = mosq_test.gen_suback(mid, 1, proto_ver=5)



helper_connect = mosq_test.gen_connect("helper", proto_ver=5)
helper_connack = mosq_test.gen_connack(rc=0, proto_ver=5)

mid=1
props = mqtt5_props.gen_uint32_prop(mqtt5_props.PROP_MESSAGE_EXPIRY_INTERVAL, 1)
publish1s_packet = mosq_test.gen_publish("subpub/qos1", mid=mid, qos=1, payload="message1", proto_ver=5, properties=props)
puback1s_packet = mosq_test.gen_puback(mid)

mid=2
props = mqtt5_props.gen_uint32_prop(mqtt5_props.PROP_MESSAGE_EXPIRY_INTERVAL, 10)
publish2s_packet = mosq_test.gen_publish("subpub/qos1", mid=mid, qos=1, payload="message2", proto_ver=5, properties=props)
puback2s_packet = mosq_test.gen_puback(mid)


port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    sock = mosq_test.do_client_connect(connect_packet, connack1_packet, timeout=20, port=port)
    mosq_test.do_send_receive(sock, subscribe_packet, suback_packet, "suback")
    sock.close()

    helper = mosq_test.do_client_connect(helper_connect, helper_connack, timeout=20, port=port)
    mosq_test.do_send_receive(helper, publish1s_packet, puback1s_packet, "puback 1")
    mosq_test.do_send_receive(helper, publish2s_packet, puback2s_packet, "puback 2")

    time.sleep(2)
    
    sock = mosq_test.do_client_connect(connect_packet, connack2_packet, timeout=20, port=port)
    packet = sock.recv(len(publish2s_packet))
    for i in range(9, 5, -1):
        props = mqtt5_props.gen_uint32_prop(mqtt5_props.PROP_MESSAGE_EXPIRY_INTERVAL, i)
        publish2r_packet = mosq_test.gen_publish("subpub/qos1", mid=2, qos=1, payload="message2", proto_ver=5, properties=props)
        if packet == publish2r_packet:
            rc = 0
            break

    sock.close()
finally:
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))

exit(rc)

