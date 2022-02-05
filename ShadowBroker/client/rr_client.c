/*
Copyright (c) 2009-2018 Roger Light <roger@atchoo.org>

All rights reserved. This program and the accompanying materials
are made available under the terms of the Eclipse Public License v1.0
and Eclipse Distribution License v1.0 which accompany this distribution.
 
The Eclipse Public License is available at
   http://www.eclipse.org/legal/epl-v10.html
and the Eclipse Distribution License is available at
  http://www.eclipse.org/org/documents/edl-v10.php.
 
Contributors:
   Roger Light - initial implementation and documentation.
*/

#include "config.h"

#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#ifndef WIN32
#include <unistd.h>
#include <signal.h>
#else
#include <process.h>
#include <winsock2.h>
#define snprintf sprintf_s
#endif

#include <mosquitto.h>
#include <mqtt_protocol.h>
#include "client_shared.h"
#include "pub_shared.h"

enum rr__state {
	rr_s_new,
	rr_s_connected,
	rr_s_subscribed,
	rr_s_ready_to_publish,
	rr_s_wait_for_response,
	rr_s_disconnect
};

static enum rr__state client_state = rr_s_new;

extern struct mosq_config cfg;

bool process_messages = true;
int msg_count = 0;
struct mosquitto *mosq = NULL;

#ifndef WIN32
void my_signal_handler(int signum)
{
	if(signum == SIGALRM){
		process_messages = false;
		mosquitto_disconnect_v5(mosq, MQTT_RC_DISCONNECT_WITH_WILL_MSG, cfg.disconnect_props);
	}
}
#endif

void print_message(struct mosq_config *cfg, const struct mosquitto_message *message);


int my_publish(struct mosquitto *mosq, int *mid, const char *topic, int payloadlen, void *payload, int qos, bool retain)
{
	return mosquitto_publish_v5(mosq, mid, topic, payloadlen, payload, qos, retain, cfg.publish_props);
}


void my_message_callback(struct mosquitto *mosq, void *obj, const struct mosquitto_message *message, const mosquitto_property *properties)
{
	print_message(&cfg, message);
	switch(cfg.pub_mode){
		case MSGMODE_CMD:
		case MSGMODE_FILE:
		case MSGMODE_STDIN_FILE:
		case MSGMODE_NULL:
			client_state = rr_s_disconnect;
			break;
		case MSGMODE_STDIN_LINE:
			client_state = rr_s_ready_to_publish;
			break;
	}
	/* FIXME - check all below
	if(process_messages == false) return;

	if(cfg.retained_only && !message->retain && process_messages){
		process_messages = false;
		mosquitto_disconnect_v5(mosq, 0, cfg.disconnect_props);
		return;
	}

	if(message->retain && cfg.no_retain) return;
	if(cfg.filter_outs){
		for(i=0; i<cfg.filter_out_count; i++){
			mosquitto_topic_matches_sub(cfg.filter_outs[i], message->topic, &res);
			if(res) return;
		}
	}

	//print_message(&cfg, message);

	if(cfg.msg_count>0){
		msg_count++;
		if(cfg.msg_count == msg_count){
			process_messages = false;
			mosquitto_disconnect_v5(mosq, 0, cfg.disconnect_props);
		}
	}
	*/
}

void my_connect_callback(struct mosquitto *mosq, void *obj, int result, int flags, const mosquitto_property *properties)
{
	if(!result){
		client_state = rr_s_connected;
		mosquitto_subscribe_v5(mosq, NULL, cfg.response_topic, cfg.qos, 0, cfg.subscribe_props);
	}else{
		client_state = rr_s_disconnect;
		if(result){
			if(result == MQTT_RC_UNSUPPORTED_PROTOCOL_VERSION){
				err_printf(&cfg, "Connection error: %s. mosquitto_rr only supports connecting to an MQTT v5 broker\n", mosquitto_reason_string(result));
			}else{
				err_printf(&cfg, "Connection error: %s\n", mosquitto_reason_string(result));
			}
		}
		mosquitto_disconnect_v5(mosq, 0, cfg.disconnect_props);
	}
}


void my_subscribe_callback(struct mosquitto *mosq, void *obj, int mid, int qos_count, const int *granted_qos)
{
	if(granted_qos[0] < 128){
		client_state = rr_s_ready_to_publish;
	}else{
		client_state = rr_s_disconnect;
		err_printf(&cfg, "%s\n", mosquitto_reason_string(granted_qos[0]));
		mosquitto_disconnect_v5(mosq, 0, cfg.disconnect_props);
	}
}


void my_publish_callback(struct mosquitto *mosq, void *obj, int mid, int reason_code, const mosquitto_property *properties)
{
	client_state = rr_s_wait_for_response;
}


void print_usage(void)
{
	int major, minor, revision;

	mosquitto_lib_version(&major, &minor, &revision);
	printf("mosquitto_rr is an mqtt client that can be used to publish a request message and wait for a response.\n");
	printf("             Defaults to MQTT v5, where the Request-Response feature will be used, but v3.1.1 can also be used\n");
	printf("             with v3.1.1 brokers.\n");
	printf("mosquitto_rr version %s running on libmosquitto %d.%d.%d.\n\n", VERSION, major, minor, revision);
	printf("Usage: mosquitto_rr {[-h host] [-p port] [-u username] [-P password] -t topic | -L URL} -e response-topic\n");
	printf("                    [-c] [-k keepalive] [-q qos] [-R]\n");
	printf("                    [-F format]\n");
#ifndef WIN32
	printf("                    [-W timeout_secs]\n");
#endif
#ifdef WITH_SRV
	printf("                    [-A bind_address] [-S]\n");
#else
	printf("                    [-A bind_address]\n");
#endif
	printf("                    [-i id] [-I id_prefix]\n");
	printf("                    [-d] [-N] [--quiet] [-v]\n");
	printf("                    [--will-topic [--will-payload payload] [--will-qos qos] [--will-retain]]\n");
#ifdef WITH_TLS
	printf("                    [{--cafile file | --capath dir} [--cert file] [--key file]\n");
	printf("                      [--ciphers ciphers] [--insecure]\n");
	printf("                      [--tls-alpn protocol]\n");
	printf("                      [--tls-engine engine] [--keyform keyform] [--tls-engine-kpass-sha1]]\n");
#ifdef FINAL_WITH_TLS_PSK
	printf("                     [--psk hex-key --psk-identity identity [--ciphers ciphers]]\n");
#endif
#endif
#ifdef WITH_SOCKS
	printf("                    [--proxy socks-url]\n");
#endif
	printf("                    [-D command identifier value]\n");
	printf("       mosquitto_rr --help\n\n");
	printf(" -A : bind the outgoing socket to this host/ip address. Use to control which interface\n");
	printf("      the client communicates over.\n");
	printf(" -c : disable 'clean session' (store subscription and pending messages when client disconnects).\n");
	printf(" -d : enable debug messages.\n");
	printf(" -D : Define MQTT v5 properties. See the documentation for more details.\n");
	printf(" -F : output format.\n");
	printf(" -h : mqtt host to connect to. Defaults to localhost.\n");
	printf(" -i : id to use for this client. Defaults to mosquitto_rr_ appended with the process id.\n");
	printf(" -k : keep alive in seconds for this client. Defaults to 60.\n");
	printf(" -L : specify user, password, hostname, port and topic as a URL in the form:\n");
	printf("      mqtt(s)://[username[:password]@]host[:port]/topic\n");
	printf(" -N : do not add an end of line character when printing the payload.\n");
	printf(" -p : network port to connect to. Defaults to 1883 for plain MQTT and 8883 for MQTT over TLS.\n");
	printf(" -P : provide a password\n");
	printf(" -q : quality of service level to use for communications. Defaults to 0.\n");
	printf(" -R : do not print stale messages (those with retain set).\n");
#ifdef WITH_SRV
	printf(" -S : use SRV lookups to determine which host to connect to.\n");
#endif
	printf(" -t : mqtt response topic to subscribe to. May be repeated multiple times.\n");
	printf(" -u : provide a username\n");
	printf(" -v : print received messages verbosely.\n");
	printf(" -V : specify the version of the MQTT protocol to use when connecting.\n");
	printf("      Defaults to 5.\n");
#ifndef WIN32
	printf(" -W : Specifies a timeout in seconds how long to wait for a response.\n");
#endif
	printf(" --help : display this message.\n");
	printf(" --quiet : don't print error messages.\n");
	printf(" --will-payload : payload for the client Will, which is sent by the broker in case of\n");
	printf("                  unexpected disconnection. If not given and will-topic is set, a zero\n");
	printf("                  length message will be sent.\n");
	printf(" --will-qos : QoS level for the client Will.\n");
	printf(" --will-retain : if given, make the client Will retained.\n");
	printf(" --will-topic : the topic on which to publish the client Will.\n");
#ifdef WITH_TLS
	printf(" --cafile : path to a file containing trusted CA certificates to enable encrypted\n");
	printf("            certificate based communication.\n");
	printf(" --capath : path to a directory containing trusted CA certificates to enable encrypted\n");
	printf("            communication.\n");
	printf(" --cert : client certificate for authentication, if required by server.\n");
	printf(" --key : client private key for authentication, if required by server.\n");
	printf(" --ciphers : openssl compatible list of TLS ciphers to support.\n");
	printf(" --tls-version : TLS protocol version, can be one of tlsv1.2 tlsv1.1 or tlsv1.\n");
	printf("                 Defaults to tlsv1.2 if available.\n");
	printf(" --insecure : do not check that the server certificate hostname matches the remote\n");
	printf("              hostname. Using this option means that you cannot be sure that the\n");
	printf("              remote host is the server you wish to connect to and so is insecure.\n");
	printf("              Do not use this option in a production environment.\n");
#ifdef WITH_TLS_PSK
	printf(" --psk : pre-shared-key in hexadecimal (no leading 0x) to enable TLS-PSK mode.\n");
	printf(" --psk-identity : client identity string for TLS-PSK mode.\n");
#endif
#endif
#ifdef WITH_SOCKS
	printf(" --proxy : SOCKS5 proxy URL of the form:\n");
	printf("           socks5h://[username[:password]@]hostname[:port]\n");
	printf("           Only \"none\" and \"username\" authentication is supported.\n");
#endif
	printf("\nSee https://mosquitto.org/ for more information.\n\n");
}

int main(int argc, char *argv[])
{
	int rc;
#ifndef WIN32
		struct sigaction sigact;
#endif

	mosquitto_lib_init();

	rc = client_config_load(&cfg, CLIENT_RR, argc, argv);
	if(rc){
		if(rc == 2){
			/* --help */
			print_usage();
		}else{
			fprintf(stderr, "\nUse 'mosquitto_rr --help' to see usage.\n");
		}
		goto cleanup;
	}

	if(!cfg.topic || cfg.pub_mode == MSGMODE_NONE || !cfg.response_topic){
		fprintf(stderr, "Error: All of topic, message, and response topic must be supplied.\n");
		fprintf(stderr, "\nUse 'mosquitto_rr --help' to see usage.\n");
		goto cleanup;
	}
	rc = mosquitto_property_add_string(&cfg.publish_props, MQTT_PROP_RESPONSE_TOPIC, cfg.response_topic);
	if(rc){
		fprintf(stderr, "Error adding property RESPONSE_TOPIC.\n");
		goto cleanup;
	}
	rc = mosquitto_property_check_all(CMD_PUBLISH, cfg.publish_props);
	if(rc){
		err_printf(&cfg, "Error in PUBLISH properties: Duplicate response topic.\n");
		goto cleanup;
	}

	if(client_id_generate(&cfg)){
		goto cleanup;
	}

	mosq = mosquitto_new(cfg.id, cfg.clean_session, &cfg);
	if(!mosq){
		switch(errno){
			case ENOMEM:
				err_printf(&cfg, "Error: Out of memory.\n");
				break;
			case EINVAL:
				err_printf(&cfg, "Error: Invalid id and/or clean_session.\n");
				break;
		}
		goto cleanup;
	}
	if(client_opts_set(mosq, &cfg)){
		goto cleanup;
	}
	if(cfg.debug){
		mosquitto_log_callback_set(mosq, my_log_callback);
	}
	mosquitto_connect_v5_callback_set(mosq, my_connect_callback);
	mosquitto_subscribe_callback_set(mosq, my_subscribe_callback);
	mosquitto_message_v5_callback_set(mosq, my_message_callback);

	rc = client_connect(mosq, &cfg);
	if(rc){
		goto cleanup;
	}

#ifndef WIN32
	sigact.sa_handler = my_signal_handler;
	sigemptyset(&sigact.sa_mask);
	sigact.sa_flags = 0;

	if(sigaction(SIGALRM, &sigact, NULL) == -1){
		perror("sigaction");
		goto cleanup;
	}

	if(cfg.timeout){
		alarm(cfg.timeout);
	}
#endif

	do{
		rc = mosquitto_loop(mosq, -1, 1);
		if(client_state == rr_s_ready_to_publish){
			client_state = rr_s_wait_for_response;
			switch(cfg.pub_mode){
				case MSGMODE_CMD:
				case MSGMODE_FILE:
				case MSGMODE_STDIN_FILE:
					rc = my_publish(mosq, &mid_sent, cfg.topic, cfg.msglen, cfg.message, cfg.qos, cfg.retain);
					break;
				case MSGMODE_NULL:
					rc = my_publish(mosq, &mid_sent, cfg.topic, 0, NULL, cfg.qos, cfg.retain);
					break;
				case MSGMODE_STDIN_LINE:
					/* FIXME */
					break;
			}
		}
	}while(rc == MOSQ_ERR_SUCCESS && client_state != rr_s_disconnect);

	mosquitto_destroy(mosq);
	mosquitto_lib_cleanup();

	if(cfg.msg_count>0 && rc == MOSQ_ERR_NO_CONN){
		rc = 0;
	}
	client_config_cleanup(&cfg);
	if(rc){
		err_printf(&cfg, "Error: %s\n", mosquitto_strerror(rc));
	}
	return rc;

cleanup:
	mosquitto_lib_cleanup();
	client_config_cleanup(&cfg);
	return 1;
}

