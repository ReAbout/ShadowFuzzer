#!/usr/bin/env python3

# Test whether a client subscribed to a topic receives its own message sent to that topic.
# And whether the no-local option is persisted.

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
props = mqtt5_props.gen_uint32_prop(mqtt5_props.PROP_SESSION_EXPIRY_INTERVAL, 100)
connect_packet = mosq_test.gen_connect(
    "persistent-subscription-test", keepalive=keepalive, clean_session=False, proto_ver=5, properties=props
)
connack_packet = mosq_test.gen_connack(rc=0, proto_ver=5)
connack_packet2 = mosq_test.gen_connack(rc=0, flags=1, proto_ver=5)  # session present

mid = 1
subscribe1_packet = mosq_test.gen_subscribe(mid, "subpub/nolocal", 5, proto_ver=5)
suback1_packet = mosq_test.gen_suback(mid, 1, proto_ver=5)

mid = 2
subscribe2_packet = mosq_test.gen_subscribe(mid, "subpub/local", 1, proto_ver=5)
suback2_packet = mosq_test.gen_suback(mid, 1, proto_ver=5)

mid = 1
publish1_packet = mosq_test.gen_publish("subpub/nolocal", qos=1, mid=mid, payload="message", proto_ver=5)
puback1_packet = mosq_test.gen_puback(mid, proto_ver=5)

mid = 2
publish2s_packet = mosq_test.gen_publish("subpub/local", qos=1, mid=mid, payload="message", proto_ver=5)
puback2s_packet = mosq_test.gen_puback(mid, proto_ver=5)

mid = 1
publish2a_packet = mosq_test.gen_publish("subpub/local", qos=1, mid=mid, payload="message", proto_ver=5)
puback2a_packet = mosq_test.gen_puback(mid, proto_ver=5)

mid = 2
publish2b_packet = mosq_test.gen_publish("subpub/local", qos=1, mid=mid, payload="message", proto_ver=5)
puback2b_packet = mosq_test.gen_puback(mid, proto_ver=5)

if os.path.exists('mosquitto-%d.db' % (port)):
    os.unlink('mosquitto-%d.db' % (port))

broker = mosq_test.start_broker(filename=os.path.basename(__file__), use_conf=True, port=port)

(stdo1, stde1) = ("", "")
try:
    sock = mosq_test.do_client_connect(connect_packet, connack_packet, timeout=20, port=port)
    mosq_test.do_send_receive(sock, subscribe1_packet, suback1_packet, "suback1")
    mosq_test.do_send_receive(sock, subscribe2_packet, suback2_packet, "suback2")

    mosq_test.do_send_receive(sock, publish1_packet, puback1_packet, "puback1a")
    mosq_test.do_send_receive(sock, publish2s_packet, puback2s_packet, "puback2a")

    if mosq_test.expect_packet(sock, "publish2a", publish2a_packet):
        sock.send(puback2a_packet)

        broker.terminate()
        broker.wait()
        (stdo1, stde1) = broker.communicate()
        sock.close()

        broker = mosq_test.start_broker(filename=os.path.basename(__file__), use_conf=True, port=port)

        sock = mosq_test.do_client_connect(connect_packet, connack_packet2, timeout=20, port=port)

        mosq_test.do_send_receive(sock, publish1_packet, puback1_packet, "puback1b")
        mosq_test.do_send_receive(sock, publish2s_packet, puback2s_packet, "puback2b")

        if mosq_test.expect_packet(sock, "publish2b", publish2b_packet):
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

