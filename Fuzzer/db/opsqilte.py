import sqlite3,logging
import config
from lib.utils import dump


class opsqlite:
    def __init__(self,db_path):
        logging.debug('DB of sqlite connect '+ db_path)
        self.conn = sqlite3.connect(db_path)
        self.cur = self.conn.cursor()
    def executemany(self,sql,value_list):
        logging.debug('SQL: '+ sql)
        try:
            self.cur.executemany(sql,value_list)
            self.conn.commit()
        except sqlite3.Error as e:
            logging.error(e)
        result = self.cur.fetchall()
        logging.debug('Result ' + str(dump(result)))
        return result
    def execute(self,sql):
        logging.debug('SQL: '+ sql)
        try:
            self.cur.execute(sql)
            self.conn.commit()
        except sqlite3.Error as e:
            logging.error(e)
        result = self.cur.fetchall()
        logging.debug('Result ' + str(dump(result)))
        return result
    def empty(self,table_name):
        sql = "delete from [{}]".format(table_name)
        self.execute(sql)
        sql_seq = "update sqlite_sequence set seq=0 where name='{}'".format(table_name)
        self.execute(sql_seq)
    def __del__(self):
        self.conn.close()

