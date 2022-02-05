#!/usr/bin/env python3

# Check whether a v5 client handles a v5 PUBACK with all combinations
# of with/without reason code and properties.

from mosq_test_helper import *

def len_test(test, puback_packet):
    port = mosq_test.get_lib_port()

    rc = 1
    keepalive = 60
    connect_packet = mosq_test.gen_connect("publish-qos1-test", keepalive=keepalive, proto_ver=5)
    connack_packet = mosq_test.gen_connack(rc=0, proto_ver=5)

    disconnect_packet = mosq_test.gen_disconnect(proto_ver=5)

    mid = 1
    publish_packet = mosq_test.gen_publish("pub/qos1/test", qos=1, mid=mid, payload="message", proto_ver=5)

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
        conn.settimeout(15)

        if mosq_test.expect_packet(conn, "connect", connect_packet):
            conn.send(connack_packet)

            if mosq_test.expect_packet(conn, "publish", publish_packet):
                conn.send(puback_packet)

                if mosq_test.expect_packet(conn, "disconnect", disconnect_packet):
                    rc = 0

        conn.close()
    finally:
        client.terminate()
        client.wait()
        sock.close()

    if rc != 0:
        print(test)
        exit(rc)


# No reason code, no properties
puback_packet = mosq_test.gen_puback(1)
len_test("qos1 len 2", puback_packet)

# Reason code, no properties
puback_packet = mosq_test.gen_puback(1, proto_ver=5, reason_code=0x00)
len_test("qos1 len 3", puback_packet)

# Reason code, empty properties
puback_packet = mosq_test.gen_puback(1, proto_ver=5, reason_code=0x00, properties="")
len_test("qos1 len 4", puback_packet)

# Reason code, one property
props = mqtt5_props.gen_string_pair_prop(mqtt5_props.PROP_USER_PROPERTY, "key", "value")
puback_packet = mosq_test.gen_puback(1, proto_ver=5, reason_code=0x00, properties=props)
len_test("qos1 len >5", puback_packet)
