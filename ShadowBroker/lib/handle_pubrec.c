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

#include <assert.h>
#include <stdio.h>
#include <string.h>

#ifdef WITH_BROKER
#  include "mosquitto_broker_internal.h"
#endif

#include "mosquitto.h"
#include "logging_mosq.h"
#include "memory_mosq.h"
#include "messages_mosq.h"
#include "mqtt_protocol.h"
#include "net_mosq.h"
#include "packet_mosq.h"
#include "read_handle.h"
#include "send_mosq.h"
#include "util_mosq.h"

int handle__pubrec(struct mosquitto_db *db, struct mosquitto *mosq)
{
	uint8_t reason_code = 0;
	uint16_t mid;
	int rc;
	mosquitto_property *properties = NULL;
	int state;

	assert(mosq);

	state = mosquitto__get_state(mosq);
	if(state != mosq_cs_active){
		return MOSQ_ERR_PROTOCOL;
	}

	rc = packet__read_uint16(&mosq->in_packet, &mid);
	if(rc) return rc;
	if(mid == 0) return MOSQ_ERR_PROTOCOL;

	if(mosq->protocol == mosq_p_mqtt5 && mosq->in_packet.remaining_length > 2){
		rc = packet__read_byte(&mosq->in_packet, &reason_code);
		if(rc) return rc;

		if(mosq->in_packet.remaining_length > 3){
			rc = property__read_all(CMD_PUBREC, &mosq->in_packet, &properties);
			if(rc) return rc;
			/* Immediately free, we don't do anything with Reason String or User Property at the moment */
			mosquitto_property_free_all(&properties);
		}
	}

#ifdef WITH_BROKER
	log__printf(NULL, MOSQ_LOG_DEBUG, "Received PUBREC from %s (Mid: %d)", mosq->id, mid);

	if(reason_code < 0x80){
		rc = db__message_update_outgoing(mosq, mid, mosq_ms_wait_for_pubcomp, 2);
	}else{
		return db__message_delete_outgoing(db, mosq, mid, mosq_ms_wait_for_pubrec, 2);
	}
#else
	UNUSED(db);

	log__printf(mosq, MOSQ_LOG_DEBUG, "Client %s received PUBREC (Mid: %d)", mosq->id, mid);

	if(reason_code < 0x80 || mosq->protocol != mosq_p_mqtt5){
		rc = message__out_update(mosq, mid, mosq_ms_wait_for_pubcomp, 2);
	}else{
		if(!message__delete(mosq, mid, mosq_md_out, 2)){
			/* Only inform the client the message has been sent once. */
			pthread_mutex_lock(&mosq->callback_mutex);
			if(mosq->on_publish_v5){
				mosq->in_callback = true;
				mosq->on_publish_v5(mosq, mosq->userdata, mid, reason_code, properties);
				mosq->in_callback = false;
			}
			pthread_mutex_unlock(&mosq->callback_mutex);
		}
		util__increment_send_quota(mosq);
		pthread_mutex_lock(&mosq->msgs_out.mutex);
		message__release_to_inflight(mosq, mosq_md_out);
		pthread_mutex_unlock(&mosq->msgs_out.mutex);
		return MOSQ_ERR_SUCCESS;
	}
#endif
	if(rc == MOSQ_ERR_NOT_FOUND){
		log__printf(mosq, MOSQ_LOG_WARNING, "Warning: Received PUBREC from %s for an unknown packet identifier %d.", mosq->id, mid);
	}else if(rc != MOSQ_ERR_SUCCESS){
		return rc;
	}
	rc = send__pubrel(mosq, mid);
	if(rc) return rc;

	return MOSQ_ERR_SUCCESS;
}

