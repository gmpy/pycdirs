# pycdirs

pycdirs 是 [cdirs](https://github.com/gmpy/cdirs) 的 python 实现和加强版本，主要用于 中&英 环境的快速的目录跳转。

pycdirs 的主要目标群体是中文用户，因此不管提交还是注释，都尽可能使用中文。这个工具有以下特点：

- 支持拼音匹配
- 支持模糊匹配
- 支持标签跳转
- 支持历史跳转
- 支持Tab补全


******

### 　　　　　　　　　　　　Author: 广漠飘羽
### 　　　　　　　　　 E-mail: gmpy_tiger@163.com

******

## 1. 目录

- [简介](#2-简介)
- [快速安装](#3-快速安装)
- [命令集](#4-命令集)
- [使用示例](#5-使用示例)
- [TODO](#6-TODO)
- [参考资料](#7-参考资料)

## 2. 简介

在中英环境跳转目录，频繁切换中英输入一度让我非常苦恼。为什么不打造一个适合 中&英 环境的跳转工具呢？在这个想法下催生了 pycdirs。在使用过程中逐步优化了更多的体验细节，目标是打造一个更适合中国人习惯的目录跳转工具。

在设计这个工具时，继承了 cdirs 的标签跳转，参考了 z 的历史记录跳转，拓展了拼音和模糊匹配，还有更多的小细节，希望能给你我带来愉悦的使用体验。

这个工具核心能力基于 Python 开发，引用了开源的模糊匹配、拼音匹配工具。Python 并不是我的主语言，算法也不是我的长项，优化执行速度稍显得力不从心。当前功能可用，偶尔出现跳转慢，也不够丝滑，盼有志之士施以援手。

## 3. 快速安装

### 3.1 安装 Python3

此工具基于 Python3 开发，使用者需要安装 Python3 的环境。对现代大多数系统来说，Python3 已经预安装了，如果很不幸你的环境被阉割了此工具，可通过以下命令安装。

```
# mac
brew install python3

# ubuntu
sudo apt install python3
sudo apt install python3-pip
```

### 3.2 安装依赖的 Python 工具

```
pip3 install thefuzz pypinyin
```

### 3.3 安装 pycdirs

在 **~/.zsh** 或者 **~/.bash** 中添加以下命令，重新开新窗口即可。

```
_CDIRS_CMD=cd
source /path/for/pycdirs/cdirs.sh
```

上述命令会取代 cd，这是建议用法。当然，如果希望保留原始的 cd，只需要使用以下的命令，通过 ```cdirs``` 使用。

```
source /path/for/pycdirs/cdirs.sh
```

## 4. 命令集

```Bash
usage: pycdirs.py [--help] [-s [,标签]] [-l [,标签]] [-d ,标签] [--complete] [-h]
                  [path [path ...]]

positional arguments:
  path                  目标跳转的目录、标签等关键词

optional arguments:
  --help                展示此消息后退出
  -s [,标签], --set-label [,标签]
                        设置标签(标签必须以','开头)，参数缺省则当前路径为快速标签
  -l [,标签], --list-label [,标签]
                        列出匹配的标签后退出，缺省列出所有标签
  -d ,标签, --del-label ,标签
                        删除标签(标签必须以','开头)，参数缺省则删除快速标签
  --complete            打印补全列表，用于支持Tab补全
  -h, --list-history    列出匹配的历史目录，缺省列出所有历史目录

一个更适合中文环境的目录跳转工具，支持标签和历史记录，支持模糊匹配，也支持中文
```

## 5. 使用示例

### 5.1 拼音跳转

拼音支持三种匹配模式：

1. 完整拼音
2. 首字母
3. 元音字母

```Bash
# 例如目录：./安卓，以下命令都可以跳转（当前目录的拼音匹配）
$ cd anzhuo # 完整拼音
$ cd az # 首字母
$ cd anzh # 元音字母

# 例如目录：projects/安卓/builds，以下命令都可以跳转（历史记录的拼音匹配）
$ cd projects/anzhuo/builds # 完整拼音
$ cd projects/az/builds # 首字母
$ cd projects/anzh/builds # 元音字母
```

### 5.2 cd 的继承

pycdirs 可以完全取代 cd，因此 cd 跳转的方法都可以使用：

```
# 跳转到指定目录
$ cd /home/gmpy/projects
$ cd ~/gmpy/projects
$ cd ./projects
$ cd ..

# 跳转到用户目录
$ cd
$ cd ~

# 跳转到上一次目录
$ cd -
```

### 5.3 历史记录与多参数精准跳转

pycdirs 会自动记录所有去过的目录，并参考 z 的方法基于频率和时间打分。在操作中会跳转到分数最高的目录。

```
# 假设有这么个历史记录中目录：~/projects/x/customer/app/src/entry，可以通过以下命令跳转：
$ cd entry # 在历史目录中匹配 entry
$ cd ent # 在历史目录中模糊匹配
$ cd x entry # 在历史目录记录中正则匹配 "x.*entry"
```

当然，如果当前目录与历史记录有重名，会优先当前目录，这才符合使用习惯。

```
# 假设存在历史目录：~/projects/linux，以及当前目录有子目录 ./linux
$ cd linux # 会优先跳转到 ./linux 而非历史记录的 ~/projects/linux
```

### 5.4 给目录打上标签

pycdirs 可以给目录打上个全局的标签，后面通过标签跳转。标签都以英文逗号 ',' 开头。一次打标所有终端共享。

```
# 给常用目录打标，标签名为 ,rootfs
$ cd -s ,rootfs ~/project/x/path/for/rootfs

# 给当前目录打标，标签名为 ,config
$ cd ~/project/x/path/for/config
$ cd -s ,config
```

除了上述固定的标签外，我们经常会遇到需要临时切到其他目录执行操作，然后再返回的情况。这时候，我们可以用快速标签。

```
# 快捷打标，',' 是一个特殊的标签，建议在需要临时切到其他目录前使用。
$ cd ,, # 此方法把当前目录标记下来
$ cd -s , # 等效于 'cd ,,'
```

只要打上了标签，都可以快速跳转到标签。

```
$ cd ,config # 跳转到 ,config 标记的目录 ~/project/x/path/for/config
$ cd ,rootfs # 跳转到 ,rootfs 标记的目录 ~/project/x/path/for/rootfs
$ cd , # 跳转到快速标签 , 标记的目录
```

### 5.5 列出历史目录和标签

pycdirs 可以自动记录所有去过的目录，通过以下命令可以打印出历史目录，第一列是目录基于时间与频次的打分，第二列是具体目录。打分分数越高，优先级越高。

```
# 列出所有历史目录
$ cd -h

# 列出匹配的历史目录，等效于 cd 跳转的预演
$ cd -h entry
```

也可以打印所有记录的标签。请记得，所有标签都以 ',' 开头。

```
# 列出所有标签
$ cd -l
# 列出匹配的标签
$ cd -l ,config
$ cd -l ,con # 模糊匹配规则，把所有模糊匹配的标签都列出来
```

## 6. TODO

* 支持 zsh 补全
* 优化拼音和模糊检索性能
* 优化 python 的效率

## 7. 参考资料

* z：优秀的基于历史记录的跳转工具：[https://github.com/rupa/z](https://github.com/rupa/z)
* autojump：优秀的基于历史记录的跳转工具：[https://github.com/wting/autojump](https://github.com/wting/autojump)
* cdirs: 基于标签的跳转工具，pycdirs 的前身：[https://github.com/gmpy/cdirs](https://github.com/gmpy/cdirs)
* pypinyin：采用的中文转拼音工具：[https://github.com/mozillazg/python-pinyin](https://github.com/mozillazg/python-pinyin)
* thefuzz：采用的模糊匹配工具：[https://github.com/seatgeek/thefuzz](https://github.com/seatgeek/thefuzz)
