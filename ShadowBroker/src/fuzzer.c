/*
[Fuzz] Fuzzer for MQTT Client.
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sqlite3.h>
#include <arpa/inet.h>
#include <sys/types.h>
#include <sys/un.h>
#include <sys/socket.h>
#include <netinet/ip.h>
#include <netinet/ip_icmp.h>
#include <unistd.h>
#include <sys/time.h>
#include <pthread.h>

#include "fuzzer.h"
#include "mosquitto_broker_internal.h"

#define SOCK_PATH "/var/run/fuzzer.sock"
#define SOCK_BUF_SIZE 1024
#define SQL_SIZE 2048

sqlite3 *fuzzer_db = NULL;   
char *fuzz_client_ip = NULL;
char *fuzz_ping_from_ip = NULL;
char *fuzz_db_file = NULL;
char *fuzz_avoid_clientid = NULL;


/*
typedef struct {
    long time;
    int vul_type;
    int needStop;
} vul_message;

int fuzz_notify_fuzzer(long timev, int vul_type, int needStop){  //type 1: crash; type 2:cmd injection
    int uds_fd;
    struct sockaddr_un servaddr;
    vul_message vulmsg;
    int msg_len;
    int ret = 0;

    if((uds_fd = socket(AF_UNIX, SOCK_STREAM, 0)) < 0){
        log__printf(NULL, MOSQ_LOG_ERR, "[Fuzz] Can't Create UNIX DOMAIN SOCKET.");
        return 0;
    }
    memset(&servaddr, 0, sizeof(servaddr));
    servaddr.sun_family = AF_UNIX;
    strcpy(servaddr.sun_path, SOCK_PATH);
    
    if(connect(uds_fd, (struct sockaddr *)&servaddr, sizeof(servaddr)) < 0){
        log__printf(NULL, MOSQ_LOG_ERR, "[Fuzz] Can't Connect to UNIX DOMAIN SOCKET.");
        return 0;
    }
    vulmsg.time = timev;
    vulmsg.vul_type = vul_type;
    vulmsg.needStop = needStop;
    msg_len = sizeof(vulmsg);
    // memcpy(buf, &vulmsg, msg_len);
    
    if(send(uds_fd, &vulmsg, msg_len, 0) <= 0){
        log__printf(NULL, MOSQ_LOG_ERR, "[Fuzz] Can't Send vul_message to UNIX DOMAIN SOCKET.");
        return 0;
    }
    close(uds_fd);
    log__printf(NULL, MOSQ_LOG_INFO, "[Fuzz] Send vul_message to fuzzer, time: %ld, vultype: %d, needStop: %d", timev, vul_type, needStop);

    return 1;
}*/

//通过sqlite向python通告漏洞信息
int fuzz_notify_fuzzer(int vul_type, bool needStop){  //type 1: crash; type 2:cmd injection
    char insert_sql[SQL_SIZE];
    memset(insert_sql, 0, SQL_SIZE);
    int rc = 0;
    char *sql = NULL;
    char *zErrMsg = NULL;
    struct timeval tv;
    long curtime;

    gettimeofday(&tv, NULL);
    curtime = tv.tv_sec*1000000 + tv.tv_usec;

    log__printf(NULL, MOSQ_LOG_ERR, "[Fuzz] VUL FOUND! TYPE: %d.", vul_type);
    if(needStop)
        sql = "insert into vulmessage (time,vul_type,need_stop) values (%ld,%d,1);";
    else
        sql = "insert into vulmessage (time,vul_type,need_stop) values (%ld,%d,0);";
    snprintf(insert_sql,
            SQL_SIZE,
            sql,
            curtime,
            vul_type);
    
    rc = sqlite3_exec(fuzzer_db, insert_sql, NULL, 0, &zErrMsg);
    if(rc != SQLITE_OK){
        log__printf(NULL, MOSQ_LOG_ERR, "[Fuzz] insert vul_message to db failed, SQL error: %s.", zErrMsg);
        sqlite3_free(zErrMsg);
        return 0;
    }
    else{
        log__printf(NULL, MOSQ_LOG_ERR, "[Fuzz] insert vul_message to db successfully.");
    }
    return 1;
}

//监听icmp，判断命令注入
void *fuzz_handle_cmd_injection(){
    int sockfd, n;
    socklen_t clilen;
    struct sockaddr_in cliaddr;
    char buf[1024];
    char *srchost = NULL;
    struct in_addr in_host;
    
    struct icmphdr *icmp_hdr = NULL;
    struct iphdr *ip_hdr=NULL;
    
    sockfd = socket(AF_INET, SOCK_RAW, IPPROTO_ICMP);
    if(sockfd < 0){
        log__printf(NULL, MOSQ_LOG_ERR, "[Fuzz] Create socket error.");
        exit(0);
    }
    clilen = sizeof(struct sockaddr_in);
    while(1){
        n = recvfrom(sockfd, buf, 1024, 0, (struct sockaddr *)&cliaddr, &clilen);
        if(n < 0){
            log__printf(NULL, MOSQ_LOG_ERR, "[Fuzz] recv ICMP failed.");
            exit(0);
        }
        ip_hdr = (struct iphdr *)buf;
        memcpy(&in_host, &ip_hdr->saddr, 4);
        srchost = inet_ntoa(in_host);
        icmp_hdr = (struct icmphdr*) ((char*)ip_hdr + (4*ip_hdr->ihl));
        if(icmp_hdr && ip_hdr){
            if(icmp_hdr->type==ICMP_ECHO && (!strcmp(srchost, fuzz_ping_from_ip))){
                fuzz_notify_fuzzer(2, false);
            }
        }
    }
}

//抓取消息，保存至sqlite数据库中
void fuzz_sqlite_insert_message(char *ip_addr, char *clientid, char *topic, bool is_pub, void *payload, int pay_len){
    char insert_sql[SQL_SIZE];
    int rc = 0;
    char *zErrMsg = NULL;
    memset(insert_sql, 0, SQL_SIZE);

    if(!fuzzer_db){
        log__printf(NULL, MOSQ_LOG_ERR, "[Fuzz] sqlite has not been init, insert failed!");
        return;
    }
    
    if(!is_pub){   //insert subscribe data
        snprintf(insert_sql, 
            SQL_SIZE, 
            "insert into message (ip_addr,clientid,topic,is_pub) values ('%s','%s','%s',0);",
            ip_addr,
            clientid,
            topic);
        rc = sqlite3_exec(fuzzer_db, insert_sql, NULL, 0, &zErrMsg);
        if(rc != SQLITE_OK){
            log__printf(NULL, MOSQ_LOG_ERR, "[Fuzz] insert subscribe message to db failed, SQL error: %s.", zErrMsg);
            sqlite3_free(zErrMsg);
        }
        else{
            log__printf(NULL, MOSQ_LOG_ERR, "[Fuzz] insert subscribe message to db successfully.");
        }
    }
    else{         //insert publish data
        sqlite3_stmt *stmt = NULL;
        snprintf(insert_sql, 
            SQL_SIZE, 
            "insert into message (ip_addr,clientid,topic,is_pub, payload) values ('%s','%s','%s',1,?);",
            ip_addr,
            clientid,
            topic);
        rc = sqlite3_prepare_v2(fuzzer_db, insert_sql, -1, &stmt, NULL);
        if(rc==SQLITE_OK && stmt){
            rc = sqlite3_bind_blob(stmt, 1, payload, pay_len, NULL);
            if(rc != SQLITE_OK){
                log__printf(NULL, MOSQ_LOG_ERR, "[Fuzz] bind blob failed, rc: %d.", rc);
                if(stmt){
                    sqlite3_finalize(stmt);
                }
                return;
            }
            else{
                rc = sqlite3_step(stmt);
                if(rc != SQLITE_DONE){
                    log__printf(NULL, MOSQ_LOG_ERR, "[Fuzz] blob step failed, rc: %d.", rc);
                    if(stmt){
                        sqlite3_finalize(stmt);
                    }
                    return;
                }
                else{
                    log__printf(NULL, MOSQ_LOG_ERR, "[Fuzz] insert publish message to db successfully.");
                }
            }
        }
        else{
            log__printf(NULL, MOSQ_LOG_ERR, "[Fuzz] prepare blob message to db failed, rc: %d.", rc);
            return;
        }
        if(stmt){
            sqlite3_finalize(stmt);
            stmt = NULL;
        }
    }
}

//初始化sqlite数据库
void fuzz_sqlite_init(){
    //init sqlite3
    char *zErrMsg = NULL; 
    bool is_file_exist = false;
    int rc=0;
    char * create_message_sql = "CREATE TABLE [message](" \
                "id INTEGER PRIMARY KEY AUTOINCREMENT, " \
                "ip_addr VARCHAR(255), " \
                "clientid VARCHAR(255), " \
                "topic VARCHAR(255), " \
                "is_pub BOOL, " \
                "payload BLOB);";

    char * create_notify_sql = "CREATE TABLE [vulmessage](" \
                "time INT64 PRIMARY KEY, " \
                "vul_type INT(1), " \
                "need_stop BOOL);";

    if(!fuzz_db_file){
        log__printf(NULL, MOSQ_LOG_ERR, "[Fuzz] fuzz_db_file is NULL.");
        exit(0);
    }
    if(!access(fuzz_db_file,F_OK)){
        is_file_exist = true;
        log__printf(NULL, MOSQ_LOG_ERR, "[Fuzz] DB File Existed.");
    }
    else
        is_file_exist = false;
    rc = sqlite3_open(fuzz_db_file, &fuzzer_db);
    if(rc){
        log__printf(NULL, MOSQ_LOG_ERR, "[Fuzz] Can't open sqlite db.");
        exit(0);
    }
    //If message table has been created, do not create again.
    if(!is_file_exist){
        rc = sqlite3_exec(fuzzer_db, create_message_sql, 0, 0, &zErrMsg);
        if(rc != SQLITE_OK){
            log__printf(NULL, MOSQ_LOG_ERR, "[Fuzz] Create table message Failed.");
            sqlite3_free(zErrMsg);
            exit(0);
        }
        
        rc = sqlite3_exec(fuzzer_db, create_notify_sql, 0, 0, &zErrMsg);
        if(rc != SQLITE_OK){
            log__printf(NULL, MOSQ_LOG_ERR, "[Fuzz] Create table vulmessage Failed.");
            sqlite3_free(zErrMsg);
            exit(0);
        }
    }
}

void fuzzer_init(){
    pthread_t ntid;
    int rc;
    fuzz_sqlite_init();
    //fuzz_handle_cmd_injection();

    rc = pthread_create(&ntid, NULL, fuzz_handle_cmd_injection, NULL);
    if(rc != 0){
        log__printf(NULL, MOSQ_LOG_ERR, "[Fuzz] Create ICMP Listen thread failed.");
        exit(0);
    }
}