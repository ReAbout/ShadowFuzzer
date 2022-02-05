#!/usr/bin/env python3

# Test whether a connection is disconnected if it sets the will flag but does
# not provide a will payload.

from mosq_test_helper import *

rc = 1
keepalive = 10
connect_packet = mosq_test.gen_connect("will-no-payload", keepalive=keepalive, will_topic="will/topic", will_qos=1, will_retain=True)
b = list(struct.unpack("B"*len(connect_packet), connect_packet))

bmod = b[0:len(b)-2]
bmod[1] = bmod[1] - 2 # Reduce remaining length by two to remove final two payload length values

connect_packet = struct.pack("B"*len(bmod), *bmod)

port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    sock = mosq_test.do_client_connect(connect_packet, b"", port=port)
    sock.close()
    rc = 0
finally:
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))

exit(rc)

