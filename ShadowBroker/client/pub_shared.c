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

#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifndef WIN32
#include <time.h>
#else
#include <process.h>
#include <winsock2.h>
#define snprintf sprintf_s
#endif

#include <mosquitto.h>
#include <mqtt_protocol.h>
#include "client_shared.h"
#include "pub_shared.h"

/* Global variables for use in callbacks. See sub_client.c for an example of
 * using a struct to hold variables for use in callbacks. */
int mid_sent = -1;
struct mosq_config cfg;

void my_log_callback(struct mosquitto *mosq, void *obj, int level, const char *str)
{
	UNUSED(mosq);
	UNUSED(obj);
	UNUSED(level);

	printf("%s\n", str);
}

int load_stdin(void)
{
	long pos = 0, rlen;
	char buf[1024];
	char *aux_message = NULL;

	cfg.pub_mode = MSGMODE_STDIN_FILE;

	while(!feof(stdin)){
		rlen = fread(buf, 1, 1024, stdin);
		aux_message = realloc(cfg.message, pos+rlen);
		if(!aux_message){
			err_printf(&cfg, "Error: Out of memory.\n");
			free(cfg.message);
			return 1;
		} else
		{
			cfg.message = aux_message;
		}
		memcpy(&(cfg.message[pos]), buf, rlen);
		pos += rlen;
	}
	cfg.msglen = pos;

	if(!cfg.msglen){
		err_printf(&cfg, "Error: Zero length input.\n");
		return 1;
	}

	return 0;
}

int load_file(const char *filename)
{
	long pos, rlen;
	FILE *fptr = NULL;

	fptr = fopen(filename, "rb");
	if(!fptr){
		err_printf(&cfg, "Error: Unable to open file \"%s\".\n", filename);
		return 1;
	}
	cfg.pub_mode = MSGMODE_FILE;
	fseek(fptr, 0, SEEK_END);
	cfg.msglen = ftell(fptr);
	if(cfg.msglen > 268435455){
		fclose(fptr);
		err_printf(&cfg, "Error: File \"%s\" is too large (>268,435,455 bytes).\n", filename);
		return 1;
	}else if(cfg.msglen == 0){
		fclose(fptr);
		err_printf(&cfg, "Error: File \"%s\" is empty.\n", filename);
		return 1;
	}else if(cfg.msglen < 0){
		fclose(fptr);
		err_printf(&cfg, "Error: Unable to determine size of file \"%s\".\n", filename);
		return 1;
	}
	fseek(fptr, 0, SEEK_SET);
	cfg.message = malloc(cfg.msglen);
	if(!cfg.message){
		fclose(fptr);
		err_printf(&cfg, "Error: Out of memory.\n");
		return 1;
	}
	pos = 0;
	while(pos < cfg.msglen){
		rlen = fread(&(cfg.message[pos]), sizeof(char), cfg.msglen-pos, fptr);
		pos += rlen;
	}
	fclose(fptr);
	return 0;
}


