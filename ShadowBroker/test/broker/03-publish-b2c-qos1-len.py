#!/usr/bin/env python3

# Check whether the broker handles a v5 PUBACK with all combinations
# of with/without reason code and properties.

from mosq_test_helper import *

def len_test(test, puback_packet):
    port = mosq_test.get_port()

    rc = 1
    mid = 3265
    keepalive = 60
    connect_packet = mosq_test.gen_connect("pub-qos1-test", keepalive=keepalive, clean_session=False, proto_ver=5)
    connack_packet = mosq_test.gen_connack(flags=0, rc=0, proto_ver=5)

    subscribe_packet = mosq_test.gen_subscribe(mid, "qos1/len/test", 1, proto_ver=5)
    suback_packet = mosq_test.gen_suback(mid, 1, proto_ver=5)

    mid = 1
    publish_packet = mosq_test.gen_publish("qos1/len/test", qos=1, mid=mid, payload="len-message", proto_ver=5)

    broker = mosq_test.start_broker(filename=os.path.basename(__file__), port=port)

    try:
        sock = mosq_test.do_client_connect(connect_packet, connack_packet, port=port)

        mosq_test.do_send_receive(sock, subscribe_packet, suback_packet, "suback")

        pub = subprocess.Popen(['./03-publish-b2c-qos1-len-helper.py', str(port)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        pub.wait()
        (stdo, stde) = pub.communicate()
        # Should have now received a publish command

        if mosq_test.expect_packet(sock, "publish", publish_packet):
            sock.send(puback_packet)

            mosq_test.do_ping(sock)
            rc = 0

        sock.close()
    finally:
        broker.terminate()
        broker.wait()
        (stdo, stde) = broker.communicate()
        if rc:
            print(stde.decode('utf-8'))

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
