#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import os
import sys
import time
import argparse
from thefuzz import process as fuzz
from pypinyin import pinyin as py
from pypinyin import Style as pystyle

CONF_LABEL = os.getenv("HOME") + "/.cdirs_label"
CONF_HISTORY = os.getenv("HOME") + "/.cdirs_history"

def parse_args():
    argp = argparse.ArgumentParser(add_help=False)
    argp.descritption = "更符合中文习惯的目录跳转工具"
    argp.add_argument("-h", "--help", action="help",
            help="展示此消息后退出")
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
    argp.add_argument("--record-history", action="store_true", dest="history",
            help="记录历史目录")
    argp.add_argument("path", type=str, nargs="?", default=os.getenv("PWD"),
            help="目标跳转的目录、标签等关键词")
    argp.epilog="一个更适合中文环境的目录跳转工具，支持标签和历史记录，支持模糊匹配，也支持中文"
    return vars(argp.parse_args(sys.argv[1:]))

def load_labels():
    labels = {}

    if os.path.exists(CONF_LABEL) and not os.path.isfile(CONF_LABEL):
        raise(f"%s 已经存在且不是文件，请删除后使用标签功能" % CONF_LABEL)
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
        raise(f"%s 已经存在且不是文件，请删除后使用标签功能" % CONF_HISTORY)
    if not os.path.exists(CONF_HISTORY):
        with open(CONF_HISTORY, "w") as f:
            pass
        return hist

    with open(CONF_HISTORY, "r") as f:
        for conf in f:
            path, freq, tm = conf.strip().split('|')
            if enable_frecent:
                hist[path] = frecent(int(freq), int(tm))
            else:
                hist[path] = (int(freq), int(tm))
    return hist

def set_label(arg):
    target_label = arg["set_label"]
    if target_label[0] != ",":
        raise ValueError("标签必须以','开头")

    labels = load_labels()
    with open(CONF_LABEL + "_tmp", "w") as f:
        print(f"[set] %s : %s" % (target_label, arg["path"]))
        f.write(f"%s|%s\n" % (target_label, arg["path"]))
        for label, path in labels.items():
            if label == target_label:
                continue
            f.write(f"%s|%s\n" % (label, path))
        os.rename(CONF_LABEL + "_tmp", CONF_LABEL)

def list_label(arg):
    target_label = arg["list_label"]
    labels = load_labels()

    if target_label is not "":
        if target_label is ',':
            if ',' in labels:
                print(f",\t%s" % labels[','])
        else:
            for label, score in fuzz.extract(target_label, labels.keys()):
                if score > 1:
                    print(f"%s\t%s" % (label, labels[label]))
    else:
        if ',' in labels:
            print(f",\t%s" % labels[','])
        for label, path in labels.items():
            if label is not ',':
                print(f"%s\t%s" % (label, path))

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
                print(f"[del] %s : %s" % (target_label, arg["path"]))
            else:
                f.write(f"%s|%s\n" % (label, path))
        os.rename(CONF_LABEL + "_tmp", CONF_LABEL)

def complete(arg):
    pass

def record_history(arg):
    target_path = os.path.abspath(arg["path"]).rstrip('/\\')

    hists = load_history()
    target_freq = (hists[target_path][0] if target_path in hists else 0) + 1
    target_tm = int(time.time())
    with open(CONF_HISTORY + "_tmp", "w") as f:
        f.write(f"%s|%d|%d\n" % (target_path, target_freq, target_tm))
        for path, (freq, tm) in hists.items():
            # remove NOT exist directory each time
            if path != target_path and os.path.isdir(path):
                f.write(f"%s|%d|%d\n" % (path, freq, tm))
    os.rename(CONF_HISTORY + "_tmp", CONF_HISTORY)

def split_single_path(path):
    out = []
    if path == '/':
        return [path]
    out.append(path)
    out.extend(split_single_path(os.path.dirname(path)))
    return out

def split_history():
    hists = load_history(enable_frecent=True)
    out = {}
    for path in hists:
        for one in split_single_path(path):
            if one not in out.keys():
                out[one] = hists[path]
            elif out[one] < hists[path]:
                out[one] = hists[path]
    return out

def frecent(rank, tm):
    """
    Reference to z.sh
    See also: https://github.com/rupa/z
    """
    dx = int(time.time()) - tm;
    return int(10000 * rank * (3.75/((0.0001 * dx + 1) + 0.25)))

def jump_label(target):
    if target[0] != ',':
        return None

    labels = load_labels()
    if target is ',':
        if ',' in labels:
            return labels[',']
    else:
        label, score = fuzz.extractOne(target, labels.keys())
        if score >= 90:
            return labels[label]

    print(f"找不到标签: %s" % target)
    exit(1)

def jump_local(target):
    entries = [ entry for entry in os.listdir(".") if os.path.isdir(entry) ]
    match_path, score = fuzz.extractOne(target, entries)
    if score >= 90:
        print(match_path)
        return

def jump_history(target):
    pathes = split_history()
    match_path_list = fuzz.extractBests(target, pathes.keys(), score_cutoff=60)
    if len(match_path_list) == 0:
        return None

    best_match_precent = 0
    best_match_length = 0
    best_match_path = ""
    for path, score in match_path_list:
        if pathes[path] >= best_match_precent:
            if pathes[path] == best_match_precent and best_match_length < len(path):
                continue
            best_match_precent = pathes[path]
            best_match_length = len(path)
            best_match_path = path
    return best_match_path


def jump_directory(arg):
    target = arg["path"]

    if target in ["~", ".", ".."] or os.path.exists(target):
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
    print(best_match)
    if best_match != None:
        print(best_match)
        return

    print(f"找不到匹配的目录: %s" % target)
    exit(1)

def main():
    arg = parse_args()
    if arg["set_label"] != None:
        set_label(arg)
    elif arg["list_label"] != None:
        list_label(arg)
    elif arg["del_label"] != None:
        delete_label(arg)
    elif arg["complete"] == True:
        complete(arg)
    elif arg["history"] == True:
        record_history(arg)
    else:
        jump_directory(arg)

if __name__ == "__main__":
    main()
