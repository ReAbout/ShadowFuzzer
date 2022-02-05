#!/usr/bin/env python3

# Test whether a clean session client has a QoS 1 message queued for it.

from mosq_test_helper import *

rc = 1
mid = 109
keepalive = 60
connect_packet = mosq_test.gen_connect("clean-qos2-test", keepalive=keepalive, clean_session=False)
connack1_packet = mosq_test.gen_connack(flags=0, rc=0)
connack2_packet = mosq_test.gen_connack(flags=1, rc=0)

disconnect_packet = mosq_test.gen_disconnect()

subscribe_packet = mosq_test.gen_subscribe(mid, "qos1/clean_session/test", 1)
suback_packet = mosq_test.gen_suback(mid, 1)

mid = 1
publish_packet = mosq_test.gen_publish("qos1/clean_session/test", qos=1, mid=mid, payload="clean-session-message")
puback_packet = mosq_test.gen_puback(mid)

port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    sock = mosq_test.do_client_connect(connect_packet, connack1_packet, port=port)
    mosq_test.do_send_receive(sock, subscribe_packet, suback_packet, "suback")

    sock.send(disconnect_packet)
    sock.close()

    pub = subprocess.Popen(['./05-clean-session-qos1-helper.py', str(port)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pub.wait()
    (stdo, stde) = pub.communicate()

    # Now reconnect and expect a publish message.
    sock = mosq_test.do_client_connect(connect_packet, connack2_packet, timeout=30, port=port)
    if mosq_test.expect_packet(sock, "publish", publish_packet):
        sock.send(puback_packet)
        rc = 0

    sock.close()
finally:
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))

exit(rc)

