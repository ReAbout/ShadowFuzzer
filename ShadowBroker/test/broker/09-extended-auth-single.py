#!/usr/bin/env python3

# Multi tests for extended auth with a single step.
# * Error in plugin
# * No matching authentication method
# * Matching authentication method, but auth rejected
# * Matching authentication method, auth succeeds
# * Matching authentication method, auth succeeds, new auth data sent back to client


from mosq_test_helper import *

def write_config(filename, port):
    with open(filename, 'w') as f:
        f.write("port %d\n" % (port))
        f.write("auth_plugin c/auth_plugin_extended_single.so\n")

port = mosq_test.get_port()
conf_file = os.path.basename(__file__).replace('.py', '.conf')
write_config(conf_file, port)

rc = 1

# Single, error in plugin
props = mqtt5_props.gen_string_prop(mqtt5_props.PROP_AUTHENTICATION_METHOD, "error")
connect1_packet = mosq_test.gen_connect("client-params-test1", keepalive=42, proto_ver=5, properties=props)

# Single, no matching authentication method
props = mqtt5_props.gen_string_prop(mqtt5_props.PROP_AUTHENTICATION_METHOD, "non-matching")
connect2_packet = mosq_test.gen_connect("client-params-test2", keepalive=42, proto_ver=5, properties=props)
connack2_packet = mosq_test.gen_connack(rc=mqtt5_rc.MQTT_RC_BAD_AUTHENTICATION_METHOD, proto_ver=5, properties=None)

# Single step, matching method, failure
props = mqtt5_props.gen_string_prop(mqtt5_props.PROP_AUTHENTICATION_METHOD, "single")
props += mqtt5_props.gen_string_prop(mqtt5_props.PROP_AUTHENTICATION_DATA, "baddata")
connect3_packet = mosq_test.gen_connect("client-params-test3", keepalive=42, proto_ver=5, properties=props)
connack3_packet = mosq_test.gen_connack(rc=mqtt5_rc.MQTT_RC_NOT_AUTHORIZED, proto_ver=5, properties=None)

# Single step, matching method, success
props = mqtt5_props.gen_string_prop(mqtt5_props.PROP_AUTHENTICATION_METHOD, "single")
props += mqtt5_props.gen_string_prop(mqtt5_props.PROP_AUTHENTICATION_DATA, "data")
connect4_packet = mosq_test.gen_connect("client-params-test5", keepalive=42, proto_ver=5, properties=props)
props = mqtt5_props.gen_string_prop(mqtt5_props.PROP_AUTHENTICATION_METHOD, "single")
connack4_packet = mosq_test.gen_connack(rc=0, proto_ver=5, properties=props)

# Single step, matching method, success, auth data back to client
props = mqtt5_props.gen_string_prop(mqtt5_props.PROP_AUTHENTICATION_METHOD, "mirror")
props += mqtt5_props.gen_string_prop(mqtt5_props.PROP_AUTHENTICATION_DATA, "somedata")
connect5_packet = mosq_test.gen_connect("client-params-test6", keepalive=42, proto_ver=5, properties=props)
props = mqtt5_props.gen_string_prop(mqtt5_props.PROP_AUTHENTICATION_METHOD, "mirror")
props += mqtt5_props.gen_string_prop(mqtt5_props.PROP_AUTHENTICATION_DATA, "atademos")
connack5_packet = mosq_test.gen_connack(rc=0, proto_ver=5, properties=props)


broker = mosq_test.start_broker(filename=os.path.basename(__file__), use_conf=True, port=port)

try:
    sock = mosq_test.do_client_connect(connect1_packet, b"", timeout=20, port=port)
    sock.close()

    sock = mosq_test.do_client_connect(connect2_packet, connack2_packet, timeout=20, port=port)
    sock.close()

    sock = mosq_test.do_client_connect(connect3_packet, connack3_packet, timeout=20, port=port)
    sock.close()

    sock = mosq_test.do_client_connect(connect4_packet, connack4_packet, timeout=20, port=port)
    sock.close()

    sock = mosq_test.do_client_connect(connect5_packet, connack5_packet, timeout=20, port=port)
    sock.close()

    rc = 0
finally:
    os.remove(conf_file)
    broker.terminate()
    broker.wait()
    (stdo, stde) = broker.communicate()
    if rc:
        print(stde.decode('utf-8'))


exit(rc)

