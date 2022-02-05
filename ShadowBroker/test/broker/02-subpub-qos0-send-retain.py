#!/usr/bin/env python3

# Test whether "send retain" subscribe options work
# MQTT v5

from mosq_test_helper import *

rc = 1
keepalive = 60
connect_packet = mosq_test.gen_connect("subpub-test", keepalive=keepalive, proto_ver=5)
connack_packet = mosq_test.gen_connack(rc=0, proto_ver=5)

mid = 530
subscribe1_packet = mosq_test.gen_subscribe(mid, "subpub/always", 0 | mqtt5_opts.MQTT_SUB_OPT_SEND_RETAIN_ALWAYS, proto_ver=5)
suback1_packet = mosq_test.gen_suback(mid, 0, proto_ver=5)

mid = 531
subscribe2_packet = mosq_test.gen_subscribe(mid, "subpub/new", 0 | mqtt5_opts.MQTT_SUB_OPT_SEND_RETAIN_NEW, proto_ver=5)
suback2_packet = mosq_test.gen_suback(mid, 0, proto_ver=5)

mid = 532
subscribe3_packet = mosq_test.gen_subscribe(mid, "subpub/never", 0 | mqtt5_opts.MQTT_SUB_OPT_SEND_RETAIN_NEVER, proto_ver=5)
suback3_packet = mosq_test.gen_suback(mid, 0, proto_ver=5)


publish1_packet = mosq_test.gen_publish("subpub/always", qos=0, retain=True, payload="message", proto_ver=5)
publish2_packet = mosq_test.gen_publish("subpub/new", qos=0, retain=True, payload="message", proto_ver=5)
publish3_packet = mosq_test.gen_publish("subpub/never", qos=0, retain=True, payload="message", proto_ver=5)

publish1r1_packet = mosq_test.gen_publish("subpub/always", qos=0, retain=True, payload="message", proto_ver=5)
publish1r2_packet = mosq_test.gen_publish("subpub/always", qos=0, retain=True, payload="message", proto_ver=5)
publish2r1_packet = mosq_test.gen_publish("subpub/new", qos=0, retain=True, payload="message", proto_ver=5)
publish2r2_packet = mosq_test.gen_publish("subpub/new", qos=0, retain=False, payload="message", proto_ver=5)
publish3r1_packet = mosq_test.gen_publish("subpub/never", qos=0, retain=False, payload="message", proto_ver=5)
publish3r2_packet = mosq_test.gen_publish("subpub/never", qos=0, retain=False, payload="message", proto_ver=5)


port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    sock = mosq_test.do_client_connect(connect_packet, connack_packet, timeout=5, port=port)

    sock.send(publish1_packet)
    sock.send(publish2_packet)
    sock.send(publish3_packet)

    # Don't expect a message after this
    mosq_test.do_send_receive(sock, subscribe3_packet, suback3_packet, "suback3")
    # Don't expect a message after this
    mosq_test.do_send_receive(sock, subscribe3_packet, suback3_packet, "suback3")

    # Expect a message after this, because it is the first subscribe
    mosq_test.do_send_receive(sock, subscribe2_packet, suback2_packet, "suback2")
    if mosq_test.expect_packet(sock, "publish2r1", publish2r1_packet):
        # Don't expect a message after this, it is the second subscribe
        mosq_test.do_send_receive(sock, subscribe2_packet, suback2_packet, "suback2")

        # Always expect a message after this
        mosq_test.do_send_receive(sock, subscribe1_packet, suback1_packet, "suback1")
        if mosq_test.expect_packet(sock, "publish1r1", publish1r1_packet):
            # Always expect a message after this
            mosq_test.do_send_receive(sock, subscribe1_packet, suback1_packet, "suback1")
            if mosq_test.expect_packet(sock, "publish1r1", publish1r2_packet):
                rc = 0

    sock.close()
finally:
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))

exit(rc)

