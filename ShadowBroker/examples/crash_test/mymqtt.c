#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "mosquitto.h"
#include <unistd.h>
#include <cjson/cJSON.h>

void onConnect(struct mosquitto *mosq, void *userdata, int result){
	if(!result){
		mosquitto_subscribe(mosq, NULL, "irc/test", 1);
	}
	else
		puts("connect failed!\n");
}

void onMessage(struct mosquitto *mosq, void *userdata, const struct mosquitto_message *message){
	// char buf[10];
	// if(message->payloadlen){
	// 	printf("receive topic: %s\n", message->topic);
	// 	printf("receive payload: %s\n", (char*)message->payload);
	// 	strcpy(buf, message->payload);
	// 	printf("buf: %s\n", buf);
	// }
	cJSON *payload = NULL;
	cJSON *item = NULL;
	cJSON *params = NULL;
	char *cookie = NULL;
	char *dir = NULL;
	char buf[1024];
	char crash_str[50];
	char cmdinj_str[50];
	FILE *fpipe = NULL;
	

	memset(crash_str, 0, sizeof(crash_str));
	memset(cmdinj_str, 0, sizeof(cmdinj_str));
	memset(buf, 0, sizeof(buf));

	payload = cJSON_Parse(message->payload);
	if(payload == NULL){
		const char *error_ptr = cJSON_GetErrorPtr();
		if(error_ptr != NULL){
			fprintf(stderr, "Error before: %s\n", error_ptr);
			return;
		}
	}
	params = cJSON_GetObjectItem(payload, "params");
	//char *jsonstr = cJSON_Print(params);
	//printf("params: %s\n", jsonstr);
	item = cJSON_GetObjectItem(params, "Cookie");
	cookie = item->valuestring;
	item = cJSON_GetObjectItem(params, "Dir");
	dir = item->valuestring;
	//printf("cookie: %s, dir: %s\n", cookie, dir);

	if(cookie!=NULL){
		sprintf(crash_str, "Cookie: %s", cookie);
		//printf("%s\n", crash_str);
	}
	if(cmdinj_str!=NULL){
		snprintf(cmdinj_str, sizeof(cmdinj_str)-1, "ls %s", dir);
		//printf("cmd: %s\n",cmdinj_str);
		fpipe = popen(cmdinj_str, "r");
		fread(buf, 1, sizeof(buf), fpipe);
		//printf("cmd result: %s\n",buf);
		pclose(fpipe);
	}
}


int main(int argc, char *argv[]){
	struct mosquitto *mosq = NULL;
	char *host = argv[1];
	mosquitto_lib_init();
	mosq = mosquitto_new(NULL, true, NULL);
	mosquitto_connect_callback_set(mosq, onConnect);
	mosquitto_message_callback_set(mosq, onMessage);
	mosquitto_connect(mosq, host, 1883, 0);
	puts("working.....\n");
	while(!mosquitto_loop_forever(mosq, 0, 1)){}

//	mosquitto_disconnect(mosq);
//	mosquitto_destroy(mosq);
//	mosquitto_lib_cleanup();
	return 0;
}

