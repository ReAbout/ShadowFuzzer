#!/usr/bin/env python3

from mosq_test_helper import *

port = mosq_test.get_port()

rc = 1
mid = 3265
keepalive = 60
connect_packet = mosq_test.gen_connect("pub-qos1-disco-test", keepalive=keepalive, clean_session=False)
connack1_packet = mosq_test.gen_connack(flags=0, rc=0)
connack2_packet = mosq_test.gen_connack(flags=1, rc=0)

subscribe_packet = mosq_test.gen_subscribe(mid, "qos1/disconnect/test", 1)
suback_packet = mosq_test.gen_suback(mid, 1)

mid = 1
publish_packet = mosq_test.gen_publish("qos1/disconnect/test", qos=1, mid=mid, payload="disconnect-message")
publish_dup_packet = mosq_test.gen_publish("qos1/disconnect/test", qos=1, mid=mid, payload="disconnect-message", dup=True)
puback_packet = mosq_test.gen_puback(mid)

mid = 3266
publish2_packet = mosq_test.gen_publish("qos1/outgoing", qos=1, mid=mid, payload="outgoing-message")
puback2_packet = mosq_test.gen_puback(mid)

broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    sock = mosq_test.do_client_connect(connect_packet, connack1_packet, port=port)

    mosq_test.do_send_receive(sock, subscribe_packet, suback_packet, "suback")

    pub = subprocess.Popen(['./03-publish-b2c-disconnect-qos1-helper.py', str(port)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pub.wait()
    (stdo, stde) = pub.communicate()
    # Should have now received a publish command

    if mosq_test.expect_packet(sock, "publish", publish_packet):
        # Send our outgoing message. When we disconnect the broker
        # should get rid of it and assume we're going to retry.
        sock.send(publish2_packet)
        sock.close()

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(60) # 60 seconds timeout is much longer than 5 seconds message retry.
        sock.connect(("localhost", port))

        mosq_test.do_send_receive(sock, connect_packet, connack2_packet, "connack")

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

