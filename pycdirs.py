#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import sys
import time
import re
from argparse import ArgumentParser as argparser

CONF_LABEL = os.getenv("HOME") + "/.cdirs_label"
CONF_HISTORY = os.getenv("HOME") + "/.cdirs_history"

def parse_args():
    argp = argparser(add_help=False)
    argp.descritption = "更符合中文习惯的目录跳转工具"
    argp.add_argument("--help", action="help", help="展示此消息后退出")
    argp.add_argument("-s", "--set-label", metavar=',标签', type=str,
            dest="set_label", nargs="?", default=None, const=",",
            help="设置标签(标签必须以','开头)，参数缺省则当前路径为快速标签")
    argp.add_argument("-l", "--list-label", metavar=',标签', type=str,
            dest="list_label", nargs="?", default=None, const="",
            help="列出匹配的标签后退出，缺省列出所有标签")
    argp.add_argument("-d", "--del-label", metavar=",标签", type=str, dest="del_label",
            help="删除标签(标签必须以','开头)，参数缺省则删除快速标签")
    argp.add_argument("--complete", action="store_true", dest="complete",
            help="打印补全列表，用于支持Tab补全")
    argp.add_argument("-h", "--list-history", action="store_true", dest="list_history",
            help="列出匹配的历史目录，缺省列出所有历史目录")
    argp.add_argument("path", type=str, nargs="*", default=os.getenv("PWD"),
            help="目标跳转的目录、标签等关键词")
    argp.epilog="一个更适合中文环境的目录跳转工具，支持标签和历史记录，支持模糊匹配，也支持中文"
    return vars(argp.parse_args(sys.argv[1:]))

def load_labels():
    labels = {}

    if os.path.exists(CONF_LABEL) and not os.path.isfile(CONF_LABEL):
        raise FileExistsError("%s 已经存在且不是文件，请删除后使用标签功能" % CONF_LABEL)
    if not os.path.exists(CONF_LABEL):
        with open(CONF_LABEL, "w") as f:
            pass
        return labels

    with open(CONF_LABEL, "r") as f:
        for conf in f:
            label, path = conf.strip().split('|')
            labels[label] = path
    return labels

def load_history(enable_frecent = False):
    hist = {}

    if os.path.exists(CONF_HISTORY) and not os.path.isfile(CONF_HISTORY):
        raise FileExistsError("%s 已经存在且不是文件，请删除后使用标签功能" % CONF_HISTORY)
    if not os.path.exists(CONF_HISTORY):
        with open(CONF_HISTORY, "w") as f:
            pass
        return hist

    with open(CONF_HISTORY, "r") as f:
        for conf in f:
            path, freq, tm = conf.strip().split('|')
            if enable_frecent:
                hist[path] = frecent(float(freq), int(tm))
            else:
                hist[path] = (float(freq), int(tm))
    return hist

def set_label(arg):
    if arg["path"][0] == ",,":
        target_path = os.getenv("PWD")
        target_label = ","
    else:
        target_path = os.path.abspath(arg["path"]).rstrip('/\\')
        target_label = arg["set_label"]

    if target_label[0] != ",":
        raise ValueError("标签必须以','开头")

    labels = load_labels()
    with open(CONF_LABEL + "_tmp", "w") as f:
        print("[set] %s : %s" % (target_label, target_path))
        f.write("%s|%s\n" % (target_label, target_path))
        for label, path in labels.items():
            if label == target_label:
                continue
            f.write("%s|%s\n" % (label, path))
        os.rename(CONF_LABEL + "_tmp", CONF_LABEL)

def list_label(arg):
    target_label = arg["list_label"]
    labels = load_labels()

    if target_label != "":
        if target_label == ',':
            if ',' in labels:
                print(",\t%s" % labels[','])
        else:
            match_list = get_match(target_label, labels.keys(), score=1, count=sys.maxsize)
            for label in match_list:
                print("%s\t%s" % (label, labels[label]))
    else:
        if ',' in labels:
            print(",\t%s" % labels[','])
        for label, path in labels.items():
            if label != ',':
                print("%s\t%s" % (label, path))

def delete_label(arg):
    target_label = arg["del_label"]
    if target_label[0] != ",":
        raise ValueError("标签必须以','开头")

    labels = load_labels()
    if len(labels) == 0:
        return

    with open(CONF_LABEL + "_tmp", "w") as f:
        for label, path in labels.items():
            if label == target_label:
                print("[del] %s : %s" % (target_label, arg["path"]))
            else:
                f.write("%s|%s\n" % (label, path))
        os.rename(CONF_LABEL + "_tmp", CONF_LABEL)

def complete_label(target):
    labels = load_labels()
    if target == ',':
        print("\n".join(labels.keys()))
        return
    match_list = get_match(target, labels.keys(), score=1, count=sys.maxsize)
    if len(match_list):
        print("\n".join(match_list))

def complete_local(target):
    entries = [ entry for entry in os.listdir(".") if os.path.isdir(entry) ]
    print("\n".join(entries))

def complete_path(target):
    entries = [ entry for entry in os.listdir(".") if os.path.isdir(entry) ]
    pathes = split_history()
    match_list = get_match(target, list(pathes.keys()) + entries, score=65, count=sys.maxsize)
    if len(match_list):
        print("\n".join(match_list))

def complete(arg):
    target = arg["path"]
    if len(target) == 0:
        complete_local(target)
    elif target[0] == '/':
        return
    elif target[0] == ',':
        complete_label(target)
    else:
        complete_path(target)

def list_history(arg):
    target = None
    if arg["path"] != os.getenv("PWD"):
        arg["path"] = [ sub for p in arg["path"] for sub in p.split() ]
        arg["path"] = '.*'.join(arg["path"])
        target = arg["path"]
    pathes = split_history()
    match_list = get_match(target, pathes.keys(), score=0, count=sys.maxsize)
    if len(match_list) == 0:
        return

    match_list.sort(key = lambda match : pathes[match])
    for match in match_list:
        print("%-10d %s" % (pathes[match], match))

def split_single_path(path):
    out = []
    if path not in ('/', os.getenv("HOME")):
        out.append(path)
        out.extend(split_single_path(os.path.dirname(path)))
    return out

def split_history():
    hists = load_history(enable_frecent=True)
    out = {}
    for path in hists:
        for one in split_single_path(path):
            if one not in out.keys() or out[one] < hists[path]:
                out[one] = hists[path]
    return out

def frecent(rank, tm):
    """
    Reference to z.sh
    See also: https://github.com/rupa/z
    """
    dx = int(time.time()) - tm;
    return int(10000 * rank * (3.75/((0.0001 * dx + 1) + 0.25)))

def split_single_pinyin(py_list):
    base_list = [""]
    for words in py_list:
        base_list = [ base + one for base in base_list for one in words ]
    return base_list

def to_pinyin(words):
    from pypinyin import pinyin as py
    from pypinyin import Style as pystyle

    n_list = py(words, style=pystyle.NORMAL, heteronym=True)
    n_list = split_single_pinyin(n_list)

    f_list = py(words, style=pystyle.FIRST_LETTER, heteronym=True)
    f_list = split_single_pinyin(f_list)

    i_list = py(words, style=pystyle.INITIALS, heteronym=True)
    i_list = split_single_pinyin(i_list)

    return list(set(n_list + f_list + i_list))

def pinyin_choices(choices_list):
    out_list = []
    out_map = {}
    for choice in choices_list:
        py_out = to_pinyin(choice)
        out_map[choice] = py_out
        out_list.extend([ "".join(one) for one in py_out])
    return (out_list, out_map)

def remove_same_keep_sort(choices_list):
    out_list = []
    for one in choices_list:
        if one in out_list:
            continue
        out_list.append(one)
    return out_list

def get_match(query, choices, score = 65, count = 5, strict_match = False):
    # 如果没有需要匹配的关键词，则默认所有都匹配
    if query == None:
        return list(choices)

    # 转拼音
    py_list, py_map = pinyin_choices(choices)

    # 如果查询的字符含有大写字符，则区分大小写，否则默认全转小写
    has_uppercase = any(c.isupper() for c in query)
    if has_uppercase == False:
        query = query.lower()
        py_list = [ one.lower() for one in py_list ]
        py_map = { k: [ n.lower() for n in v ] for k, v in py_map.items() }

    # 通过正则匹配
    pattern = re.compile(query)
    match_list = [ s for s in py_list if pattern.search(s.replace(os.getenv("HOME"), "", 1)) ]
    if len(match_list):
        out_list = [ key for path in match_list for key, val in py_map.items() if path in val ]
        return remove_same_keep_sort(out_list)

    if strict_match == False:
        # 通过 theFuzz 模糊匹配
        from thefuzz import process as fuzz
        match_list = fuzz.extractBests(query, py_list, score_cutoff=score, limit=count)
        if len(match_list):
            out_list = [ key for path, score in match_list for key, val in py_map.items() if path in val ]
            return remove_same_keep_sort(out_list)

    return []

def jump_label(target):
    if target[0] != ',':
        return None

    labels = load_labels()
    if target == ',' and ',' in labels:
        return labels[',']
    elif target != ',':
        match_list = get_match(target, labels.keys(), score=90, count = 1)
        if len(match_list):
            # 如果当前目录已经是最匹配的目录了，则获取下一级匹配的，总不能跳转到当前目录吧
            if labels[match_list[0]] == os.path.abspath(os.getcwd()) and len(match_list) > 1:
                return labels[match_list[1]]
            return labels[match_list[0]]

    # ',' 开头意味着只检索标签
    print("找不到标签: %s" % target, file=sys.stderr)
    exit(1)

def jump_local(target):
    if target[0] == ',':
        return None

    if os.path.isdir(target):
        return target

    if os.path.isdir(os.path.dirname(target)):
        return os.path.dirname(target)

    entries = [ entry for entry in os.listdir(".") if os.path.isdir(entry) ]
    match_list = get_match(target, entries, score=65, count=1, strict_match=True)
    return match_list[0] if len(match_list) else None


def jump_history(target):
    pathes = split_history()
    match_list = get_match(target, pathes.keys(), score=60, count=10)
    if len(match_list) == 0:
        return None

    best_match_frecent = 0
    best_match_length = 0
    best_match_path = ""
    for match in match_list:
        # 如果当前目录已经是最匹配的目录了，则获取下一级匹配的，总不能跳转到当前目录吧
        if match == os.path.abspath(os.getcwd()) and len(match_list) > 1:
            continue
        if pathes[match] >= best_match_frecent:
            # 相同分值，取最长路径的
            if pathes[match] == best_match_frecent and best_match_length < len(match):
                continue
            best_match_frecent = pathes[match]
            best_match_length = len(match)
            best_match_path = match
    return best_match_path

def jump_directory(arg):
    arg["path"] = [ sub for p in arg["path"] for sub in p.split() ]
    arg["path"] = '.*'.join(arg["path"])
    target = arg["path"]

    if target in ("~", ".", "..", "-") or os.path.isdir(target):
        print(target)
        return

    best_match = jump_local(target)
    if best_match != None:
        print(best_match)
        return

    best_match = jump_label(target)
    if best_match != None:
        print(best_match)
        return

    best_match = jump_history(target)
    if best_match != None:
        print(best_match)
        return

    print("找不到匹配的目录: %s" % target, file=sys.stderr)
    exit(1)

def main():
    arg = parse_args()

    if arg["set_label"] != None or arg["path"][0] == ",,":
        set_label(arg)
    elif arg["list_label"] != None:
        list_label(arg)
    elif arg["del_label"] != None:
        delete_label(arg)
    elif arg["complete"] == True:
        complete(arg)
    elif arg["list_history"] == True:
        list_history(arg)
    else:
        jump_directory(arg)

if __name__ == "__main__":
    main()
