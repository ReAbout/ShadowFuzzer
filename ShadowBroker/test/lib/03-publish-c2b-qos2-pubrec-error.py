#!/usr/bin/env python3

# Test whether a client responds correctly when sending multiple PUBLISH with
# QoS 2, with the broker rejecting the first PUBLISH by setting the reason code
# in PUBACK to >= 0x80.

from mosq_test_helper import *

port = mosq_test.get_lib_port()

rc = 1
keepalive = 60
connect_packet = mosq_test.gen_connect("publish-qos2-test", keepalive=keepalive, proto_ver=5)

props = mqtt5_props.gen_uint16_prop(mqtt5_props.PROP_RECEIVE_MAXIMUM, 1)
connack_packet = mosq_test.gen_connack(rc=0, proto_ver=5, properties=props)

disconnect_packet = mosq_test.gen_disconnect(proto_ver=5)

mid = 1
publish_1_packet = mosq_test.gen_publish("topic", qos=2, mid=mid, payload="rejected", proto_ver=5)
pubrec_1_packet = mosq_test.gen_pubrec(mid, proto_ver=5, reason_code=0x80)

mid = 2
publish_2_packet = mosq_test.gen_publish("topic", qos=2, mid=mid, payload="accepted", proto_ver=5)
pubrec_2_packet = mosq_test.gen_pubrec(mid, proto_ver=5)
pubrel_2_packet = mosq_test.gen_pubrel(mid, proto_ver=5)
pubcomp_2_packet = mosq_test.gen_pubcomp(mid, proto_ver=5)

disconnect_packet = mosq_test.gen_disconnect(proto_ver=5)


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.settimeout(10)
sock.bind(('', port))
sock.listen(5)


client_args = sys.argv[1:]
env = dict(os.environ)
env['LD_LIBRARY_PATH'] = '../../lib:../../lib/cpp'
try:
    pp = env['PYTHONPATH']
except KeyError:
    pp = ''
env['PYTHONPATH'] = '../../lib/python:'+pp
client = mosq_test.start_client(filename=sys.argv[1].replace('/', '-'), cmd=client_args, env=env, port=port)


try:
    (conn, address) = sock.accept()
    conn.settimeout(10)

    if mosq_test.expect_packet(conn, "connect", connect_packet):
        conn.send(connack_packet)

        if mosq_test.expect_packet(conn, "publish 1", publish_1_packet):
                conn.send(pubrec_1_packet)

                if mosq_test.expect_packet(conn, "publish 2", publish_2_packet):
                    conn.send(pubrec_2_packet)

                    if mosq_test.expect_packet(conn, "pubrel 2", pubrel_2_packet):
                        conn.send(pubcomp_2_packet)
                        rc = 0

    conn.close()
finally:
    for i in range(0, 5):
        if client.returncode != None:
            break
        time.sleep(0.1)

    try:
        client.terminate()
    except OSError:
        pass

    client.wait()
    sock.close()
    if client.returncode != 0:
        exit(1)

exit(rc)
