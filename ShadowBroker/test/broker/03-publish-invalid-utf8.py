#!/usr/bin/env python3

# Test whether a PUBLISH to a topic with an invalid UTF-8 topic fails

from mosq_test_helper import *

rc = 1
mid = 53
keepalive = 60
connect_packet = mosq_test.gen_connect("publish-invalid-utf8", keepalive=keepalive)
connack_packet = mosq_test.gen_connack(rc=0)

publish_packet = mosq_test.gen_publish("invalid/utf8", 1, mid=mid)
b = list(struct.unpack("B"*len(publish_packet), publish_packet))
b[11] = 0 # Topic should never have a 0x0000
publish_packet = struct.pack("B"*len(b), *b)

puback_packet = mosq_test.gen_puback(mid)

port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    time.sleep(0.5)

    sock = mosq_test.do_client_connect(connect_packet, connack_packet, port=port)
    mosq_test.do_send_receive(sock, publish_packet, b"", "puback")

    rc = 0

    sock.close()
finally:
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))

exit(rc)

