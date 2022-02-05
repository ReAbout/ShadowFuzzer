#!/usr/bin/env python3

# Test whether a PUBLISH to a topic with QoS 2 results in the correct packet flow.
# With max_inflight_messages set to 1

from mosq_test_helper import *

def write_config(filename, port):
    with open(filename, 'w') as f:
        f.write("port %d\n" % (port))
        f.write("max_inflight_messages 1\n")

port = mosq_test.get_port()
conf_file = os.path.basename(__file__).replace('.py', '.conf')
write_config(conf_file, port)


rc = 1
keepalive = 60
connect_packet = mosq_test.gen_connect("pub-qos2-test", keepalive=keepalive)
connack_packet = mosq_test.gen_connack(rc=0)

mid = 312
publish_packet = mosq_test.gen_publish("pub/qos2/test", qos=2, mid=mid, payload="message")
pubrec_packet = mosq_test.gen_pubrec(mid)
pubrel_packet = mosq_test.gen_pubrel(mid)
pubcomp_packet = mosq_test.gen_pubcomp(mid)

port = mosq_test.get_port()
broker = mosq_test.start_broker(filename=os.path.basename(__file__), use_conf=True, port=port)

try:
    sock = mosq_test.do_client_connect(connect_packet, connack_packet, port=port, timeout=10)
    mosq_test.do_send_receive(sock, publish_packet, pubrec_packet, "pubrec")
    mosq_test.do_send_receive(sock, pubrel_packet, pubcomp_packet, "pubcomp")

    rc = 0

    sock.close()
finally:
    os.remove(conf_file)
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))

exit(rc)

