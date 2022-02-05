import os
import sys
sys.path.append('.') 

from db.opsqilte import opsqlite
import config 

sql_create_table = 'CREATE TABLE [task]('\
  '[id] INTEGER PRIMARY KEY AUTOINCREMENT,'\
  '[topic] VARCHAR(255),'\
  '[payload] BLOB);'

sql_create_table2 = 'CREATE TABLE [status]('\
  '[task_id] INT,'\
  '[time] INT64,'\
  '[current] BOOL);'



'''
操作message表
'''   
class optask:
    def __init__(self):
        db_path = config.TMP_PATH
        flag_exist = 1
        if not os.path.exists(db_path):
            flag_exist = 0
        self.db = opsqlite(db_path)
        if not flag_exist:
            self.db.execute(sql_create_table)
    
    def empty(self):
        self.db.empty('task')

    

    def get_task(self,start_id=0):
        base_sql = "select id,topic,payload from [task] "
        if start_id ==0:
            sql_select = base_sql 
        else:
            sql_select = base_sql + "where [id] >= {}".format(start_id)
        return self.db.execute(sql_select)
    
    def add_task(self,value_list):
        sql = "insert into [task] ([topic],[payload]) values (?,?)"
        return self.db.executemany(sql,value_list)

    def count(self):
        sql = "select count(*) from [task]"
        num, = self.db.execute(sql)[0]
        return num



