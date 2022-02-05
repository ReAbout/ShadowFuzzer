/*
Copyright (c) 2010-2018 Roger Light <roger@atchoo.org>

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

#ifdef WITH_PERSISTENCE

#ifndef WIN32
#include <arpa/inet.h>
#endif
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <utlist.h>

#include "mosquitto_broker_internal.h"
#include "memory_mosq.h"
#include "persist.h"
#include "time_mosq.h"
#include "util_mosq.h"

static uint32_t db_version;

const unsigned char magic[15] = {0x00, 0xB5, 0x00, 'm','o','s','q','u','i','t','t','o',' ','d','b'};

static int persist__restore_sub(struct mosquitto_db *db, const char *client_id, const char *sub, int qos, uint32_t identifier, int options);

static struct mosquitto *persist__find_or_add_context(struct mosquitto_db *db, const char *client_id, uint16_t last_mid)
{
	struct mosquitto *context;

	if(!client_id) return NULL;

	context = NULL;
	HASH_FIND(hh_id, db->contexts_by_id, client_id, strlen(client_id), context);
	if(!context){
		context = context__init(db, -1);
		if(!context) return NULL;
		context->id = mosquitto__strdup(client_id);
		if(!context->id){
			mosquitto__free(context);
			return NULL;
		}

		context->clean_start = false;

		HASH_ADD_KEYPTR(hh_id, db->contexts_by_id, context->id, strlen(context->id), context);
	}
	if(last_mid){
		context->last_mid = last_mid;
	}
	return context;
}


int persist__read_string_len(FILE *db_fptr, char **str, uint16_t len)
{
	char *s = NULL;

	if(len){
		s = mosquitto__malloc(len+1);
		if(!s){
			fclose(db_fptr);
			log__printf(NULL, MOSQ_LOG_ERR, "Error: Out of memory.");
			return MOSQ_ERR_NOMEM;
		}
		if(fread(s, 1, len, db_fptr) != len){
			mosquitto__free(s);
			return MOSQ_ERR_NOMEM;
		}
		s[len] = '\0';
	}

	*str = s;
	return MOSQ_ERR_SUCCESS;
}


int persist__read_string(FILE *db_fptr, char **str)
{
	uint16_t i16temp;
	uint16_t slen;

	if(fread(&i16temp, 1, sizeof(uint16_t), db_fptr) != sizeof(uint16_t)){
		return MOSQ_ERR_INVAL;
	}

	slen = ntohs(i16temp);
	return persist__read_string_len(db_fptr, str, slen);
}


static int persist__client_msg_restore(struct mosquitto_db *db, struct P_client_msg *chunk)
{
	struct mosquitto_client_msg *cmsg;
	struct mosquitto_msg_store_load *load;
	struct mosquitto *context;
	struct mosquitto_msg_data *msg_data;

	HASH_FIND(hh, db->msg_store_load, &chunk->F.store_id, sizeof(dbid_t), load);
	if(!load){
		/* Can't find message - probably expired */
		return MOSQ_ERR_SUCCESS;
	}

	cmsg = mosquitto__calloc(1, sizeof(struct mosquitto_client_msg));
	if(!cmsg){
		log__printf(NULL, MOSQ_LOG_ERR, "Error: Out of memory.");
		return MOSQ_ERR_NOMEM;
	}

	cmsg->next = NULL;
	cmsg->store = NULL;
	cmsg->mid = chunk->F.mid;
	cmsg->qos = chunk->F.qos;
	cmsg->retain = (chunk->F.retain_dup&0xF0)>>4;
	cmsg->timestamp = 0;
	cmsg->direction = chunk->F.direction;
	cmsg->state = chunk->F.state;
	cmsg->dup = chunk->F.retain_dup&0x0F;
	cmsg->properties = chunk->properties;

	cmsg->store = load->store;
	db__msg_store_ref_inc(cmsg->store);

	context = persist__find_or_add_context(db, chunk->client_id, 0);
	if(!context){
		mosquitto__free(cmsg);
		log__printf(NULL, MOSQ_LOG_ERR, "Error restoring persistent database, message store corrupt.");
		return 1;
	}

	if(cmsg->direction == mosq_md_out){
		msg_data = &context->msgs_out;
	}else{
		msg_data = &context->msgs_in;
	}

	if(chunk->F.state == mosq_ms_queued || (chunk->F.qos > 0 && msg_data->inflight_quota == 0)){
		DL_APPEND(msg_data->queued, cmsg);
	}else{
		DL_APPEND(msg_data->inflight, cmsg);
		if(chunk->F.qos > 0 && msg_data->inflight_quota > 0){
			msg_data->inflight_quota--;
		}
	}
	msg_data->msg_count++;
	msg_data->msg_bytes += cmsg->store->payloadlen;
	if(chunk->F.qos > 0){
		msg_data->msg_count12++;
		msg_data->msg_bytes12 += cmsg->store->payloadlen;
	}

	return MOSQ_ERR_SUCCESS;
}


static int persist__client_chunk_restore(struct mosquitto_db *db, FILE *db_fptr)
{
	int rc = 0;
	struct mosquitto *context;
	struct P_client chunk;

	memset(&chunk, 0, sizeof(struct P_client));

	if(db_version == 5){
		rc = persist__chunk_client_read_v5(db_fptr, &chunk);
	}else{
		rc = persist__chunk_client_read_v234(db_fptr, &chunk, db_version);
	}
	if(rc){
		fclose(db_fptr);
		return rc;
	}

	context = persist__find_or_add_context(db, chunk.client_id, chunk.F.last_mid);
	if(context){
		context->session_expiry_time = chunk.F.session_expiry_time;
		context->session_expiry_interval = chunk.F.session_expiry_interval;
		/* FIXME - we should expire clients here if they have exceeded their time */
	}else{
		rc = 1;
	}

	mosquitto__free(chunk.client_id);

	return rc;
}


static int persist__client_msg_chunk_restore(struct mosquitto_db *db, FILE *db_fptr, uint32_t length)
{
	struct P_client_msg chunk;
	int rc;

	memset(&chunk, 0, sizeof(struct P_client_msg));

	if(db_version == 5){
		rc = persist__chunk_client_msg_read_v5(db_fptr, &chunk, length);
	}else{
		rc = persist__chunk_client_msg_read_v234(db_fptr, &chunk);
	}
	if(rc){
		fclose(db_fptr);
		return rc;
	}

	rc = persist__client_msg_restore(db, &chunk);
	mosquitto__free(chunk.client_id);

	return rc;
}


static int persist__msg_store_chunk_restore(struct mosquitto_db *db, FILE *db_fptr, uint32_t length)
{
	struct P_msg_store chunk;
	struct mosquitto_msg_store *stored = NULL;
	struct mosquitto_msg_store_load *load;
	int64_t message_expiry_interval64;
	uint32_t message_expiry_interval;
	int rc = 0;
	int i;

	memset(&chunk, 0, sizeof(struct P_msg_store));

	if(db_version == 5){
		rc = persist__chunk_msg_store_read_v5(db_fptr, &chunk, length);
	}else{
		rc = persist__chunk_msg_store_read_v234(db_fptr, &chunk, db_version);
	}
	if(rc){
		fclose(db_fptr);
		return rc;
	}

	if(chunk.F.source_port){
		for(i=0; i<db->config->listener_count; i++){
			if(db->config->listeners[i].port == chunk.F.source_port){
				chunk.source.listener = &db->config->listeners[i];
				break;
			}
		}
	}
	load = mosquitto__calloc(1, sizeof(struct mosquitto_msg_store_load));
	if(!load){
		fclose(db_fptr);
		mosquitto__free(chunk.source.id);
		mosquitto__free(chunk.source.username);
		mosquitto__free(chunk.topic);
		UHPA_FREE(chunk.payload, chunk.F.payloadlen);
		log__printf(NULL, MOSQ_LOG_ERR, "Error: Out of memory.");
		return MOSQ_ERR_NOMEM;
	}

	if(chunk.F.expiry_time > 0){
		message_expiry_interval64 = chunk.F.expiry_time - time(NULL);
		if(message_expiry_interval64 < 0 || message_expiry_interval64 > UINT32_MAX){
			/* Expired message */
			mosquitto__free(chunk.source.id);
			mosquitto__free(chunk.source.username);
			mosquitto__free(chunk.topic);
			UHPA_FREE(chunk.payload, chunk.F.payloadlen);
			mosquitto__free(load);
			return MOSQ_ERR_SUCCESS;
		}else{
			message_expiry_interval = (uint32_t)message_expiry_interval64;
		}
	}else{
		message_expiry_interval = 0;
	}

	rc = db__message_store(db, &chunk.source, chunk.F.source_mid,
			chunk.topic, chunk.F.qos, chunk.F.payloadlen,
			&chunk.payload, chunk.F.retain, &stored, message_expiry_interval,
			chunk.properties, chunk.F.store_id, mosq_mo_client);

	mosquitto__free(chunk.source.id);
	mosquitto__free(chunk.source.username);
	chunk.source.id = NULL;
	chunk.source.username = NULL;

	if(rc == MOSQ_ERR_SUCCESS){
		stored->source_listener = chunk.source.listener;
		load->db_id = stored->db_id;
		load->store = stored;

		HASH_ADD(hh, db->msg_store_load, db_id, sizeof(dbid_t), load);
		return MOSQ_ERR_SUCCESS;
	}else{
		mosquitto__free(load);
		fclose(db_fptr);
		return rc;
	}
}

static int persist__retain_chunk_restore(struct mosquitto_db *db, FILE *db_fptr)
{
	struct mosquitto_msg_store_load *load;
	struct P_retain chunk;
	int rc;

	memset(&chunk, 0, sizeof(struct P_retain));

	if(db_version == 5){
		rc = persist__chunk_retain_read_v5(db_fptr, &chunk);
	}else{
		rc = persist__chunk_retain_read_v234(db_fptr, &chunk);
	}
	if(rc){
		fclose(db_fptr);
		return rc;
	}

	HASH_FIND(hh, db->msg_store_load, &chunk.F.store_id, sizeof(dbid_t), load);
	if(load){
		sub__messages_queue(db, NULL, load->store->topic, load->store->qos, load->store->retain, &load->store);
	}else{
		/* Can't find the message - probably expired */
	}
	return MOSQ_ERR_SUCCESS;
}

static int persist__sub_chunk_restore(struct mosquitto_db *db, FILE *db_fptr)
{
	struct P_sub chunk;
	int rc;

	memset(&chunk, 0, sizeof(struct P_sub));

	if(db_version == 5){
		rc = persist__chunk_sub_read_v5(db_fptr, &chunk);
	}else{
		rc = persist__chunk_sub_read_v234(db_fptr, &chunk);
	}
	if(rc){
		fclose(db_fptr);
		return rc;
	}

	rc = persist__restore_sub(db, chunk.client_id, chunk.topic, chunk.F.qos, chunk.F.identifier, chunk.F.options);

	mosquitto__free(chunk.client_id);
	mosquitto__free(chunk.topic);

	return rc;
}


int persist__chunk_header_read(FILE *db_fptr, int *chunk, int *length)
{
	if(db_version == 5){
		return persist__chunk_header_read_v5(db_fptr, chunk, length);
	}else{
		return persist__chunk_header_read_v234(db_fptr, chunk, length);
	}
}


int persist__restore(struct mosquitto_db *db)
{
	FILE *fptr;
	char header[15];
	int rc = 0;
	uint32_t crc;
	uint32_t i32temp;
	int chunk, length;
	ssize_t rlen;
	char *err;
	struct mosquitto_msg_store_load *load, *load_tmp;
	struct PF_cfg cfg_chunk;

	assert(db);
	assert(db->config);

	if(!db->config->persistence || db->config->persistence_filepath == NULL){
		return MOSQ_ERR_SUCCESS;
	}

	db->msg_store_load = NULL;

	fptr = mosquitto__fopen(db->config->persistence_filepath, "rb", false);
	if(fptr == NULL) return MOSQ_ERR_SUCCESS;
	rlen = fread(&header, 1, 15, fptr);
	if(rlen == 0){
		fclose(fptr);
		log__printf(NULL, MOSQ_LOG_WARNING, "Warning: Persistence file is empty.");
		return 0;
	}else if(rlen != 15){
		goto error;
	}
	if(!memcmp(header, magic, 15)){
		// Restore DB as normal
		read_e(fptr, &crc, sizeof(uint32_t));
		read_e(fptr, &i32temp, sizeof(uint32_t));
		db_version = ntohl(i32temp);
		/* IMPORTANT - this is where compatibility checks are made.
		 * Is your DB change still compatible with previous versions?
		 */
		if(db_version > MOSQ_DB_VERSION && db_version != 0){
			if(db_version == 4){
			}else if(db_version == 3){
				/* Addition of source_username and source_port to msg_store chunk in v4, v1.5.6 */
			}else if(db_version == 2){
				/* Addition of disconnect_t to client chunk in v3. */
			}else{
				fclose(fptr);
				log__printf(NULL, MOSQ_LOG_ERR, "Error: Unsupported persistent database format version %d (need version %d).", db_version, MOSQ_DB_VERSION);
				return 1;
			}
		}

		while(persist__chunk_header_read(fptr, &chunk, &length) == MOSQ_ERR_SUCCESS){
			switch(chunk){
				case DB_CHUNK_CFG:
					if(db_version == 5){
						if(persist__chunk_cfg_read_v5(fptr, &cfg_chunk)){
							return 1;
						}
					}else{
						if(persist__chunk_cfg_read_v234(fptr, &cfg_chunk)){
							return 1;
						}
					}
					if(cfg_chunk.dbid_size != sizeof(dbid_t)){
						log__printf(NULL, MOSQ_LOG_ERR, "Error: Incompatible database configuration (dbid size is %d bytes, expected %lu)",
								cfg_chunk.dbid_size, (unsigned long)sizeof(dbid_t));
						fclose(fptr);
						return 1;
					}
					db->last_db_id = cfg_chunk.last_db_id;
					break;

				case DB_CHUNK_MSG_STORE:
					if(persist__msg_store_chunk_restore(db, fptr, length)) return 1;
					break;

				case DB_CHUNK_CLIENT_MSG:
					if(persist__client_msg_chunk_restore(db, fptr, length)) return 1;
					break;

				case DB_CHUNK_RETAIN:
					if(persist__retain_chunk_restore(db, fptr)) return 1;
					break;

				case DB_CHUNK_SUB:
					if(persist__sub_chunk_restore(db, fptr)) return 1;
					break;

				case DB_CHUNK_CLIENT:
					if(persist__client_chunk_restore(db, fptr)) return 1;
					break;

				default:
					log__printf(NULL, MOSQ_LOG_WARNING, "Warning: Unsupported chunk \"%d\" in persistent database file. Ignoring.", chunk);
					fseek(fptr, length, SEEK_CUR);
					break;
			}
		}
		if(rlen < 0) goto error;
	}else{
		log__printf(NULL, MOSQ_LOG_ERR, "Error: Unable to restore persistent database. Unrecognised file format.");
		rc = 1;
	}

	fclose(fptr);

	HASH_ITER(hh, db->msg_store_load, load, load_tmp){
		HASH_DELETE(hh, db->msg_store_load, load);
		mosquitto__free(load);
	}
	return rc;
error:
	err = strerror(errno);
	log__printf(NULL, MOSQ_LOG_ERR, "Error: %s.", err);
	if(fptr) fclose(fptr);
	return 1;
}

static int persist__restore_sub(struct mosquitto_db *db, const char *client_id, const char *sub, int qos, uint32_t identifier, int options)
{
	struct mosquitto *context;

	assert(db);
	assert(client_id);
	assert(sub);

	context = persist__find_or_add_context(db, client_id, 0);
	if(!context) return 1;
	return sub__add(db, context, sub, qos, identifier, options, &db->subs);
}

#endif
