# !encoding=utf-8
import json

class TreeNode:
    def __init__(self, v=None):
        self.data = v 
        self.childs = [] 

def is_leaf_list(node_list):
    if isinstance(node_list,dict):
        return False
    else:
        return True

#嵌套字典转化成tree结构
def dict2tree(dic_json):
    ret = []
    #最外层是list
    if isinstance(dic_json, list):
        for dic_json_item in dic_json:
            for key,value in dic_json_item.items():
                root = TreeNode()
                if isinstance(value, dict):
                    root.data = key
                    root.childs += dict2tree(value)
                else:
                    root.data = (key,value)
                ret.append(root)
    else:
        for key,value in dic_json.items():
            root = TreeNode()
            #value = dic_json[key]
            if isinstance(value, dict):
                root.data = key
                root.childs += dict2tree(value)
            else:
                root.data = (key,value)
            ret.append(root)
    return ret

def tree2dict(root):
    ret = {}
    if not root:
        return ret
    if isinstance(root, list):
        for key in root:
            if isinstance(key.data, tuple):
                ret[key.data[0]] = key.data[1]
            else:
                ret[key.data] = tree2dict(key.childs)
    if isinstance(root, TreeNode):
        key = root.data
        ret[key] = tree2dict(root.childs)
    return ret


def traverse(node, tree, cb):
    if not node:
        return
    if isinstance(node, TreeNode):
        if isinstance(node.data, tuple):
            cb(node, tree)
            return 
        for child in node.childs:
            traverse(child,  tree, cb)
        return
    if isinstance(node, list):
        for r in node:
            traverse(r,  tree, cb)

test = """
{
  "header":{
    "funcNo": "IF010002",
    "opStation": "11.11.1.1",
    "appId": "aaaaaa",
    "deviceId": "kk",
    "ver":"wx-1.0",
    "channel": "4"
  },
  "payload": {
    "mobileTel": "13817120001"
  }
}
"""
if __name__ == "__main__":
    test_json = json.loads(test)
    print(test_json)
    tree = dict2tree(test_json)
    dic = tree2dict(tree)
    print(dic)
    print("---")

    def callback(leaf,tree):
        former = leaf.data
        leaf.data = (leaf.data[0], 'yyy') 
        print(tree2dict(tree))
        leaf.data = former     
    traverse(tree, tree, callback)