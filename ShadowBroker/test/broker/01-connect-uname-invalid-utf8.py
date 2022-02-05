#!/usr/bin/env python3

# Test whether a username with invalid UTF-8 fails.

from mosq_test_helper import *

rc = 1
keepalive = 60
connect_packet = mosq_test.gen_connect("connect-invalid-utf8", keepalive=keepalive, username="invalid/utf8")
b = list(struct.unpack("B"*len(connect_packet), connect_packet))
b[43] = 0 # Username should never have a 0x0000
connect_packet = struct.pack("B"*len(b), *b)

port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

try:
    time.sleep(0.5)

    sock = mosq_test.do_client_connect(connect_packet, b"", port=port)
    # Exception occurs if connack packet returned
    rc = 0
    sock.close()
finally:
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))

exit(rc)

