#!/usr/bin/env python3

from mosq_test_helper import *

port = mosq_test.get_lib_port()

rc = 1
keepalive = 60
connect_packet = mosq_test.gen_connect("prop-test", keepalive=keepalive, proto_ver=5)
connack_packet = mosq_test.gen_connack(rc=0, proto_ver=5)

props = mqtt5_props.gen_string_prop(mqtt5_props.PROP_CONTENT_TYPE, "application/json")
publish_packet = mosq_test.gen_publish("prop/qos0", qos=0, payload="message", proto_ver=5, properties=props)

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

        if mosq_test.expect_packet(conn, "publish", publish_packet):
            if mosq_test.expect_packet(conn, "disconnect", disconnect_packet):
                rc = 0

    conn.close()
finally:
    client.terminate()
    client.wait()
    if rc:
        (stdo, stde) = client.communicate()
        print(stde)
    sock.close()

exit(rc)
