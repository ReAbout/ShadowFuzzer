#include <time.h>

#define WITH_BROKER

#include <logging_mosq.h>
#include <memory_mosq.h>
#include <mosquitto_broker_internal.h>
#include <net_mosq.h>
#include <send_mosq.h>
#include <time_mosq.h>

extern uint64_t last_retained;
extern char *last_sub;
extern int last_qos;
extern uint32_t last_identifier;

struct mosquitto *context__init(struct mosquitto_db *db, mosq_sock_t sock)
{
	struct mosquitto *m;

	m = mosquitto__calloc(1, sizeof(struct mosquitto));
	if(m){
		m->msgs_in.inflight_maximum = 20;
		m->msgs_out.inflight_maximum = 20;
		m->msgs_in.inflight_quota = 20;
		m->msgs_out.inflight_quota = 20;
	}
	return m;
}

int db__message_store(struct mosquitto_db *db, const struct mosquitto *source, uint16_t source_mid, char *topic, int qos, uint32_t payloadlen, mosquitto__payload_uhpa *payload, int retain, struct mosquitto_msg_store **stored, uint32_t message_expiry_interval, mosquitto_property *properties, dbid_t store_id, enum mosquitto_msg_origin origin)
{
    struct mosquitto_msg_store *temp = NULL;
    int rc = MOSQ_ERR_SUCCESS;

    temp = mosquitto__calloc(1, sizeof(struct mosquitto_msg_store));
    if(!temp){
        rc = MOSQ_ERR_NOMEM;
        goto error;
    }

    if(source && source->id){
        temp->source_id = mosquitto__strdup(source->id);
    }else{
        temp->source_id = mosquitto__strdup("");
    }
    if(!temp->source_id){
        rc = MOSQ_ERR_NOMEM;
        goto error;
    }

    if(source && source->username){
        temp->source_username = mosquitto__strdup(source->username);
        if(!temp->source_username){
            rc = MOSQ_ERR_NOMEM;
            goto error;
        }
    }
    if(source){
        temp->source_listener = source->listener;
    }
    temp->source_mid = source_mid;
    temp->mid = 0;
    temp->qos = qos;
    temp->retain = retain;
    temp->topic = topic;
    topic = NULL;
    temp->payloadlen = payloadlen;
    temp->properties = properties;
    if(payloadlen){
        UHPA_MOVE(temp->payload, *payload, payloadlen);
    }else{
        temp->payload.ptr = NULL;
    }
    if(message_expiry_interval > 0){
        temp->message_expiry_time = time(NULL) + message_expiry_interval;
    }else{
        temp->message_expiry_time = 0;
    }

    temp->dest_ids = NULL;
    temp->dest_id_count = 0;
    db->msg_store_count++;
    db->msg_store_bytes += payloadlen;
    (*stored) = temp;

    if(!store_id){
        temp->db_id = ++db->last_db_id;
    }else{
        temp->db_id = store_id;
    }

	db->msg_store = temp;

    return MOSQ_ERR_SUCCESS;
error:
    mosquitto__free(topic);
    if(temp){
        mosquitto__free(temp->source_id);
        mosquitto__free(temp->source_username);
        mosquitto__free(temp->topic);
        mosquitto__free(temp);
    }
    UHPA_FREE(*payload, payloadlen);
    return rc;
}

int log__printf(struct mosquitto *mosq, int priority, const char *fmt, ...)
{
	return 0;
}

time_t mosquitto_time(void)
{
	return 123;
}

int net__socket_close(struct mosquitto_db *db, struct mosquitto *mosq)
{
	return MOSQ_ERR_SUCCESS;
}

int send__pingreq(struct mosquitto *mosq)
{
	return MOSQ_ERR_SUCCESS;
}

int sub__add(struct mosquitto_db *db, struct mosquitto *context, const char *sub, int qos, uint32_t identifier, int options, struct mosquitto__subhier **root)
{
	last_sub = strdup(sub);
	last_qos = qos;
	last_identifier = identifier;

	return MOSQ_ERR_SUCCESS;
}

int sub__messages_queue(struct mosquitto_db *db, const char *source_id, const char *topic, int qos, int retain, struct mosquitto_msg_store **stored)
{
	if(retain){
		last_retained = (*stored)->db_id;
	}
	return MOSQ_ERR_SUCCESS;
}


void db__msg_store_ref_inc(struct mosquitto_msg_store *store)
{
	store->ref_count++;
}

