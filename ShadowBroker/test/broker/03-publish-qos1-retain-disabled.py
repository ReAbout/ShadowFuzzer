#!/usr/bin/env python3

# Test whether a PUBLISH with a retain set when retains are disabled results in
# the correct DISCONNECT.

from mosq_test_helper import *

def write_config(filename, port):
    with open(filename, 'w') as f:
        f.write("port %d\n" % (port))
        f.write("retain_available false\n")

port = mosq_test.get_port()
conf_file = os.path.basename(__file__).replace('.py', '.conf')
write_config(conf_file, port)

rc = 1
mid = 1
keepalive = 60
connect_packet = mosq_test.gen_connect("pub-qos1-test", keepalive=keepalive, proto_ver=5)

props = mqtt5_props.gen_byte_prop(mqtt5_props.PROP_RETAIN_AVAILABLE, 0)
connack_packet = mosq_test.gen_connack(rc=0, proto_ver=5, properties=props)

publish_packet = mosq_test.gen_publish("pub/qos1/test", qos=1, mid=mid, payload="message", retain=True, proto_ver=5)
puback_packet = mosq_test.gen_puback(mid, proto_ver=5)

disconnect_packet = mosq_test.gen_disconnect(reason_code=154, proto_ver=5)

broker = mosq_test.start_broker(filename=os.path.basename(__file__), use_conf=True, port=port)

try:
    sock = mosq_test.do_client_connect(connect_packet, connack_packet, port=port)
    mosq_test.do_send_receive(sock, publish_packet, disconnect_packet, "disconnect")

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

