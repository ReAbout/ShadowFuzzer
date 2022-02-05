/*
Copyright (c) 2009-2019 Roger Light <roger@atchoo.org>

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

#include <stdio.h>
#include <string.h>

#include "mosquitto_broker_internal.h"
#include "memory_mosq.h"
#include "mqtt_protocol.h"
#include "packet_mosq.h"
#include "property_mosq.h"

#ifdef WITH_FUZZER
#include "fuzzer.h"
extern char *fuzz_avoid_clientid;
#endif

int handle__subscribe(struct mosquitto_db *db, struct mosquitto *context)
{
	int rc = 0;
	int rc2;
	uint16_t mid;
	char *sub;
	uint8_t subscription_options;
	uint32_t subscription_identifier = 0;
	uint8_t qos;
	uint8_t retain_handling = 0;
	uint8_t *payload = NULL, *tmp_payload;
	uint32_t payloadlen = 0;
	int len;
	int slen;
	char *sub_mount;
	mosquitto_property *properties = NULL;

	if(!context) return MOSQ_ERR_INVAL;

	if(context->state != mosq_cs_active){
		return MOSQ_ERR_PROTOCOL;
	}

	log__printf(NULL, MOSQ_LOG_DEBUG, "Received SUBSCRIBE from %s", context->id);

	if(context->protocol != mosq_p_mqtt31){
		if((context->in_packet.command&0x0F) != 0x02){
			return MOSQ_ERR_PROTOCOL;
		}
	}
	if(packet__read_uint16(&context->in_packet, &mid)) return 1;
	if(mid == 0) return MOSQ_ERR_PROTOCOL;

	if(context->protocol == mosq_p_mqtt5){
		rc = property__read_all(CMD_SUBSCRIBE, &context->in_packet, &properties);
		if(rc) return rc;

		if(mosquitto_property_read_varint(properties, MQTT_PROP_SUBSCRIPTION_IDENTIFIER,
					&subscription_identifier, false)){

			/* If the identifier was force set to 0, this is an error */
			if(subscription_identifier == 0){
				mosquitto_property_free_all(&properties);
				return MOSQ_ERR_PROTOCOL;
			}
		}

		mosquitto_property_free_all(&properties);
		/* Note - User Property not handled */
	}

	while(context->in_packet.pos < context->in_packet.remaining_length){
		sub = NULL;
		if(packet__read_string(&context->in_packet, &sub, &slen)){
			mosquitto__free(payload);
			return 1;
		}

		if(sub){
			if(!slen){
				log__printf(NULL, MOSQ_LOG_INFO,
						"Empty subscription string from %s, disconnecting.",
						context->address);
				mosquitto__free(sub);
				mosquitto__free(payload);
				return 1;
			}
#ifdef WITH_FUZZER
			if(fuzz_avoid_clientid && strcmp(context->id, fuzz_avoid_clientid))
				fuzz_sqlite_insert_message(context->address, context->id, sub, false, NULL, 0);
#endif

			if(mosquitto_sub_topic_check(sub)){
				log__printf(NULL, MOSQ_LOG_INFO,
						"Invalid subscription string from %s, disconnecting.",
						context->address);
				mosquitto__free(sub);
				mosquitto__free(payload);
				return 1;
			}

			if(packet__read_byte(&context->in_packet, &subscription_options)){
				mosquitto__free(sub);
				mosquitto__free(payload);
				return 1;
			}
			if(context->protocol == mosq_p_mqtt31 || context->protocol == mosq_p_mqtt311){
				qos = subscription_options;
				if(context->is_bridge){
					subscription_options = MQTT_SUB_OPT_RETAIN_AS_PUBLISHED | MQTT_SUB_OPT_NO_LOCAL;
				}
			}else{
				qos = subscription_options & 0x03;
				subscription_options &= 0xFC;

				retain_handling = (subscription_options & 0x30);
				if(retain_handling == 0x30 || (subscription_options & 0xC0) != 0){
					return MOSQ_ERR_PROTOCOL;
				}
			}
			if(qos > 2){
				log__printf(NULL, MOSQ_LOG_INFO,
						"Invalid QoS in subscription command from %s, disconnecting.",
						context->address);
				mosquitto__free(sub);
				mosquitto__free(payload);
				return 1;
			}


			if(context->listener && context->listener->mount_point){
				len = strlen(context->listener->mount_point) + slen + 1;
				sub_mount = mosquitto__malloc(len+1);
				if(!sub_mount){
					mosquitto__free(sub);
					mosquitto__free(payload);
					return MOSQ_ERR_NOMEM;
				}
				snprintf(sub_mount, len, "%s%s", context->listener->mount_point, sub);
				sub_mount[len] = '\0';

				mosquitto__free(sub);
				sub = sub_mount;

			}
			log__printf(NULL, MOSQ_LOG_DEBUG, "\t%s (QoS %d)", sub, qos);

			if(context->protocol != mosq_p_mqtt31){
				rc2 = mosquitto_acl_check(db, context, sub, 0, NULL, qos, false, MOSQ_ACL_SUBSCRIBE);
				switch(rc2){
					case MOSQ_ERR_SUCCESS:
						break;
					case MOSQ_ERR_ACL_DENIED:
						qos = 0x80;
						break;
					default:
						mosquitto__free(sub);
						return rc2;
				}
			}

			if(qos != 0x80){
				rc2 = sub__add(db, context, sub, qos, subscription_identifier, subscription_options, &db->subs);
				if(rc2 > 0){
					mosquitto__free(sub);
					return rc2;
				}
				if(context->protocol == mosq_p_mqtt311 || context->protocol == mosq_p_mqtt31){
					if(rc2 == MOSQ_ERR_SUCCESS || rc2 == MOSQ_ERR_SUB_EXISTS){
						if(sub__retain_queue(db, context, sub, qos, 0)) rc = 1;
					}
				}else{
					if((retain_handling == MQTT_SUB_OPT_SEND_RETAIN_ALWAYS)
							|| (rc2 == MOSQ_ERR_SUCCESS && retain_handling == MQTT_SUB_OPT_SEND_RETAIN_NEW)){

						if(sub__retain_queue(db, context, sub, qos, subscription_identifier)) rc = 1;
					}
				}

				log__printf(NULL, MOSQ_LOG_SUBSCRIBE, "%s %d %s", context->id, qos, sub);
			}
			mosquitto__free(sub);

			tmp_payload = mosquitto__realloc(payload, payloadlen + 1);
			if(tmp_payload){
				payload = tmp_payload;
				payload[payloadlen] = qos;
				payloadlen++;
			}else{
				mosquitto__free(payload);

				return MOSQ_ERR_NOMEM;
			}
		}
	}

	if(context->protocol != mosq_p_mqtt31){
		if(payloadlen == 0){
			/* No subscriptions specified, protocol error. */
			return MOSQ_ERR_PROTOCOL;
		}
	}
	if(send__suback(context, mid, payloadlen, payload)) rc = 1;
	mosquitto__free(payload);

#ifdef WITH_PERSISTENCE
	db->persistence_changes++;
#endif

	return rc;
}


