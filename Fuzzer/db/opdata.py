import os
import sys
sys.path.append('.') 

from db.opsqilte import opsqlite
import config

sql_create_table = 'CREATE TABLE [message]('\
  '[id] INTEGER PRIMARY KEY AUTOINCREMENT,'\
  '[topic] VARCHAR(255),'\
  '[payload] BLOB,'\
  '[is_pub] BOOL,'\
  '[ip_addr] VARCHAR(255),'\
  '[clientid] VARCHAR(255));'
sql_create_table2 = 'CREATE TABLE [vulmessage]('\
  '[time] INT64 PRIMARY KEY,'\
  '[vul_type] INT(1),'\
  '[need_stop] BOOL);'


'''
操作message表
'''   
class opmessage:
    def __init__(self,db_path):
        flag_exist = 1
        if not os.path.exists(db_path):
            flag_exist = 0
        self.db = opsqlite(db_path)
        if not flag_exist:
            self.db.execute(sql_create_table)
            self.db.execute(sql_create_table2)
    
    def empty(self):
        self.db.empty('message')

    
    def query_message(self,clientid="",is_pub=1):
        base_sql = "select topic,payload from [message] "
        if clientid =="":
            sql_select = base_sql + "where  [is_pub] = {}".format(is_pub)
        else:
            sql_select = base_sql + "where [clientid] = '{}' and [is_pub] = {}".format(clientid,is_pub)
        return self.db.execute(sql_select)
    
    def add_message(self,value_list):
        sql = "insert into [message] ([topic],[payload],[clientid],[is_pub]) values (?,?,?,?)"
        return self.db.executemany(sql,value_list)
    def count(self):
        sql = "select count(*) from [message]"
        num, = self.db.execute(sql)[0]
        return num



class opvulmessage:
    def __init__(self,db_path):
        flag_exist = 1
        if not os.path.exists(db_path):
            flag_exist = 0
        self.db = opsqlite(db_path)
        if not flag_exist:
            self.db.execute(sql_create_table)
            self.db.execute(sql_create_table2)
    def empty(self):
        self.db.empty('vulmessage')



    def check_vul(self):
        sql = "select [time],[vul_type],[need_stop] from [vulmessage]  order by time desc limit 0,1"
        return self.db.execute(sql)



