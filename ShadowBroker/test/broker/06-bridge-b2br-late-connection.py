#!/usr/bin/env python3

# Does a bridge queue up messages correctly if the remote broker starts up late?

from mosq_test_helper import *

def write_config(filename, port1, port2):
    with open(filename, 'w') as f:
        f.write("port %d\n" % (port2))
        f.write("\n")
        f.write("connection bridge_sample\n")
        f.write("address 127.0.0.1:%d\n" % (port1))
        f.write("topic bridge/# out 1\n")
        f.write("notifications false\n")
        f.write("bridge_attempt_unsubscribe false\n")

(port1, port2) = mosq_test.get_port(2)
conf_file = os.path.basename(__file__).replace('.py', '.conf')
write_config(conf_file, port1, port2)

rc = 1
keepalive = 60
client_id = socket.gethostname()+".bridge_sample"
connect_packet = mosq_test.gen_connect(client_id, keepalive=keepalive, clean_session=False, proto_ver=128+4)
connack_packet = mosq_test.gen_connack(rc=0)

c_connect_packet = mosq_test.gen_connect("client", keepalive=keepalive)
c_connack_packet = mosq_test.gen_connack(rc=0)

mid = 1
publish_packet = mosq_test.gen_publish("bridge/test", qos=1, mid=mid, payload="message")
puback_packet = mosq_test.gen_puback(mid)

ssock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ssock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
ssock.settimeout(40)
ssock.bind(('', port1))
ssock.listen(5)

broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port2, use_conf=True)

try:
    (bridge, address) = ssock.accept()
    bridge.settimeout(20)

    client = mosq_test.do_client_connect(c_connect_packet, c_connack_packet, timeout=20, port=port2)
    mosq_test.do_send_receive(client, publish_packet, puback_packet, "puback")
    client.close()
    # We've now sent a message to the broker that should be delivered to us via the bridge

    if mosq_test.expect_packet(bridge, "connect", connect_packet):
        bridge.send(connack_packet)

        if mosq_test.expect_packet(bridge, "publish", publish_packet):
            rc = 0

    bridge.close()
finally:
    os.remove(conf_file)
    try:
        bridge.close()
    except NameError:
        pass

    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))
    ssock.close()

exit(rc)

