/*
Copyright (c) 2018 Roger Light <roger@atchoo.org>

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
#ifndef PROPERTY_MOSQ_H
#define PROPERTY_MOSQ_H

#include "mosquitto_internal.h"
#include "mosquitto.h"

struct mqtt__string {
	char *v;
	int len;
};

struct mqtt5__property {
	struct mqtt5__property *next;
	union {
		uint8_t i8;
		uint16_t i16;
		uint32_t i32;
		uint32_t varint;
		struct mqtt__string bin;
		struct mqtt__string s;
	} value;
	struct mqtt__string name;
	int32_t identifier;
	bool client_generated;
};


int property__read_all(int command, struct mosquitto__packet *packet, mosquitto_property **property);
int property__write_all(struct mosquitto__packet *packet, const mosquitto_property *property, bool write_len);
void property__free(mosquitto_property **property);

int property__get_length(const mosquitto_property *property);
int property__get_length_all(const mosquitto_property *property);

#endif
