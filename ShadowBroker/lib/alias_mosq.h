/*
Copyright (c) 2019 Roger Light <roger@atchoo.org>

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

#ifndef ALIAS_MOSQ_H
#define ALIAS_MOSQ_H

#include "mosquitto_internal.h"

int alias__add(struct mosquitto *mosq, const char *topic, int alias);
int alias__find(struct mosquitto *mosq, char **topic, int alias);
void alias__free_all(struct mosquitto *mosq);

#endif
