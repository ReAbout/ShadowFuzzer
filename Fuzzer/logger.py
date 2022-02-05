
import datetime
class logger:
    def __init__(self,path):
        self.file_opt = open(path,"a")
    def write(self,text):
        time_stamp = datetime.datetime.now()
        log_text = "{} {} \n".format(time_stamp.strftime('%Y.%m.%d-%H:%M:%S'),text)
        self.file_opt.write(log_text)
    def __del__(self):
        self.file_opt.close()