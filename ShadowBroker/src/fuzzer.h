/*
[Fuzz] Fuzzer for MQTT Client.
*/

#ifndef FUZZER_H
#define FUZZER_H

#include <stdbool.h>

int fuzz_notify_fuzzer(int vul_type, bool needStop);
void *fuzz_handle_cmd_injection();
void fuzz_sqlite_insert_message(char *ip_addr, char *clientid, char *topic, bool is_pub, void *payload, int pay_len);
void fuzz_sqlite_init();
void fuzzer_init();



#endif