#!/usr/bin/env python3

# Test whether a SUBSCRIBE to a topic with QoS 2 results in the correct SUBACK packet.

from mosq_test_helper import *

rc = 1
mid = 3265
keepalive = 60
connect_packet = mosq_test.gen_connect("pub-qos1-timeout-test", keepalive=keepalive)
connack_packet = mosq_test.gen_connack(rc=0)

subscribe_packet = mosq_test.gen_subscribe(mid, "qos1/timeout/test", 1)
suback_packet = mosq_test.gen_suback(mid, 1)

mid = 1
publish_packet = mosq_test.gen_publish("qos1/timeout/test", qos=1, mid=mid, payload="timeout-message")
publish_dup_packet = mosq_test.gen_publish("qos1/timeout/test", qos=1, mid=mid, payload="timeout-message", dup=True)
puback_packet = mosq_test.gen_puback(mid)

broker = mosq_test.start_broker(filename=os.path.basename(__file__))

try:
    sock = mosq_test.do_client_connect(connect_packet, connack_packet)
    mosq_test.do_send_receive(sock, subscribe_packet, suback_packet, "suback")

    pub = subprocess.Popen(['./03-publish-b2c-timeout-qos1-helper.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE))
    pub.wait()
    (stdo, stde) = pub.communicate()
    # Should have now received a publish command

    if mosq_test.expect_packet(sock, "publish", publish_packet):
        # Wait for longer than 5 seconds to get republish with dup set
        # This is covered by the 8 second timeout

        if mosq_test.expect_packet(sock, "dup publish", publish_dup_packet):
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

