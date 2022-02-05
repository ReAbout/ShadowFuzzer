#!/usr/bin/env python3

# Test for CVE-2018-12546

from mosq_test_helper import *
import signal

def write_config(filename, port, per_listener):
    with open(filename, 'w') as f:
        f.write("per_listener_settings %s\n" % (per_listener))
        f.write("check_retain_source true\n")
        f.write("port %d\n" % (port))
        f.write("acl_file %s\n" % (filename.replace('.conf', '.acl')))

def write_acl_1(filename):
    with open(filename, 'w') as f:
        f.write('topic readwrite test/topic\n')

def write_acl_2(filename):
    with open(filename, 'w') as f:
        f.write('topic read test/topic\n')


def do_test(per_listener):
    conf_file = os.path.basename(__file__).replace('.py', '.conf')
    write_config(conf_file, port, per_listener)

    acl_file = os.path.basename(__file__).replace('.py', '.acl')
    write_acl_1(acl_file)


    rc = 1
    keepalive = 60
    connect_packet = mosq_test.gen_connect("retain-check", keepalive=keepalive)
    connack_packet = mosq_test.gen_connack(rc=0)

    mid = 1
    publish_packet = mosq_test.gen_publish("test/topic", qos=0, payload="retained message", retain=True)
    subscribe_packet = mosq_test.gen_subscribe(mid, "test/topic", 0)
    suback_packet = mosq_test.gen_suback(mid, 0)

    broker = mosq_test.start_broker(filename=os.path.basename(__file__), use_conf=True, port=port)

    try:
        sock = mosq_test.do_client_connect(connect_packet, connack_packet, port=port)
        sock.send(publish_packet)
        sock.close()

        sock = mosq_test.do_client_connect(connect_packet, connack_packet, port=port)
        mosq_test.do_send_receive(sock, subscribe_packet, suback_packet, "suback 1")

        if mosq_test.expect_packet(sock, "publish", publish_packet):
            sock.close()

            # Remove "write" ability
            write_acl_2(acl_file)
            broker.send_signal(signal.SIGHUP)

            sock = mosq_test.do_client_connect(connect_packet, connack_packet, port=port)
            mosq_test.do_send_receive(sock, subscribe_packet, suback_packet, "suback 2")
            # If we receive the retained message here, it is a failure.
            mosq_test.do_ping(sock)
            rc = 0

        sock.close()
    finally:
        os.remove(conf_file)
        os.remove(acl_file)
        broker.terminate()
        broker.wait()
        (stdo, stde) = broker.communicate()
        if rc:
            print(stde.decode('utf-8'))
            exit(rc)

port = mosq_test.get_port()
do_test("true")
do_test("false")
