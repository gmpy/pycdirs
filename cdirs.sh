#!/bin/bash

_cdirs() {
    local histfile="${_CDIRS_HISTORY:-$HOME/.cdirs_history}"
    local labelfile="${_CDIRS_LABEL:-$HOME/.cdirs_label}"

    # if symlink, dereference
    [ -h "$histfile" ] && histfile=$(readlink "$histfile")
    [ -h "$labelfile" ] && histfile=$(readlink "$labelfile")

    _cdirs_labels() {
        [ -f "$labelfile" ] || return

        local line
        while read line; do
            # only count directories
            [ -d "${line#*\|}" ] && echo "${line}"
        done < "$labelfile"
        return 0
    }

    _cdirs_dirs () {
        [ -f "$histfile" ] || return

        local line
        while read line; do
            # only count directories
            [ -d "${line%%\|*}" ] && echo "${line}"
        done < "$histfile"
        return 0
    }

    _cdirs_sh_complete() {
        key="$(echo $2 | \awk '{print substr($0, index($0, $2))}')"
        if [ "${key:0:1}" = "," ]; then
            _cdirs_labels | \awk -v q="$key" -F"|" '
                BEGIN {
                    if( q == tolower(q) ) imatch = 1
                    gsub(/ /, ".*", q)
                }
                {
                    if( imatch ) {
                        if( tolower($1) ~ q ) print $1
                    } else if( $1 ~ q ) print $1
                }
            ' 2>/dev/null
        else
            _cdirs_dirs | \awk -v q="$key" -F"|" '
                BEGIN {
                    if( q == tolower(q) ) imatch = 1
                    gsub(/ /, ".*", q)
                }
                {
                    if( imatch ) {
                        if( tolower($1) ~ q ) print $1
                    } else if( $1 ~ q ) print $1
                }
            ' 2>/dev/null
        fi
    }

    _cdirs_sh_add_history() {
        shift

        # $HOME and / aren't worth matching
        [ "$*" = "$HOME" -o "$*" = '/' ] && return

        # maintain the history file
        local tempfile="$histfile.$RANDOM"
        local maxlimit=200
        _cdirs_dirs | \awk -v path="$*" -v now="$(\date +%s)" -v limit=$maxlimit -F"|" '
            BEGIN {
                rank[path] = 1
                time[path] = now
                count = 0
            }
            count < limit {
                if( $1 == path ) {
                    rank[$1] = $2 + 1
                    time[$1] = now
                } else {
                    rank[$1] = $2
                    time[$1] = $3
                }
                count += 1
            }
            END {
                for( x in rank ) print x "|" rank[x] "|" time[x]
            }
        ' 2>/dev/null >| "$tempfile"
        # do our best to avoid clobbering the histfile in a race condition.
        if [ $? -ne 0 -a -f "$histfile" ]; then
            \env rm -f "$tempfile"
        else
            \env mv -f "$tempfile" "$histfile" || \env rm -f "$tempfile"
        fi
    }

    _cdirs_sh_jump_label() {
        # TODO
        builtin cd "$@"
    }

    _cdirs_sh_jump_history() {
        # TODO
        builtin cd "$@"
    }

    _cdirs_sh_jump() {
        local cd="$@"

        if [ -d "$cd" -o "${cd:0:1}" = '.' -o "${cd:0:1}" = '/' -o "${cd:0:1}" = '-' ]; then
            builtin cd "$cd"
        elif [ "${cd:0:1}" = ',' ]; then
            _cdirs_sh_jump_label "$cd"
        else
            _cdirs_sh_jump_history "$cd"
        fi
    }

    _cdirs_sh() {
        if [ "$1" = "--complete" ]; then
            _cdirs_sh_complete "$@"
        elif [ "$1" = "--add-history" ]; then
            _cdirs_sh_add_history "$@"
        else
            _cdirs_sh_jump "$@"
        fi
    }

    # make it quickly by using shell rather than python
    _cdirs_py_use_py() {
        local key dir file
        key="$@"
        dir="$(\dirname $key)"
        file="$(\basename $key)"

        [ -d "$key" -o "${key:0:1}" = '.' -o "${key:0:1}" = '/' ] && return 1
        [ -d "${dir}" ] && \ls $dir | \grep -q "$file" && return 1
        return 0
    }

    _cdirs_py_complete() {
        local key="$(echo $2 | \awk '{print substr($0, index($0, $2))}')"
        _cdirs_py_use_py "$key" && $_CDIRS_PY_PATH --complete "$key"
    }

    _cdirs_py_jump() {
        local cd="${@:-${HOME}}"
        if [ -d "$cd" -o "${cd:0:1}" = '.' -o "${cd:0:1}" = '/' -o "${cd:0:1}" = '-' ]; then
            builtin cd "$cd"
        else
            cd="$(${_CDIRS_PY_PATH} "$cd")"
            [ -d "$cd" ] && builtin cd "$cd"
        fi
    }

    _cdirs_py() {
        case "$1" in
            --complete) _cdirs_py_complete "$@";;
            --add-history)
                # make it quickly by using shell rather than python
                _cdirs_sh_add_history "$@"
                ;;
            -*)
                [ "$1" = '-' ] && _cdirs_py_jump "$@" && return
                ${_CDIRS_PY_PATH} $@
                ;;
            *)
                _cdirs_py_jump "$@"
                ;;
        esac
    }

    if [ -x "$_CDIRS_PY_PATH" ]; then
        _cdirs_py "$@"
    else
        _cdirs_sh "$@"
    fi
}

alias ${_CDIRS_CMD:-cdirs}='_cdirs 2>&1'

if type compctl >/dev/null 2>&1; then
    # zsh
    [ "$_CDIRS_NO_PROMPT_COMMAND" ] || {
        # populate directory list, avoid clobbering any other precmds.
        if [ "$_CDIRS_NO_RESOLVE_SYMLINKS" ]; then
            _cdirs_precmd() {
                (_cdirs --add-history "${PWD:a}" &)
                : $RANDOM
            }
        else
            _cdirs_precmd() {
                (_cdirs --add-history "${PWD:A}" &)
                : $RANDOM
            }
        fi
        [[ -n "${precmd_functions[(r)_cdirs_precmd]}" ]] || {
            precmd_functions[$(($#precmd_functions+1))]=_cdirs_precmd
        }
    }
    _cdirs_zsh_tab_completion() {
        # tab completion
        local compl
        read -l compl
        reply=(${(f)"$(_cdirs --complete "$compl")"})
    }
    compctl -U -K _cdirs_zsh_tab_completion ${_CDIRS_CMD:-cdirs}
    _CDIRS_PY_PATH="$(builtin cd $(dirname "$0") && pwd)/pycdirs.py"
elif type complete >/dev/null 2>&1; then
    # bash
    _CDIRS_PY_PATH="$(builtin cd $(dirname "$BASH_SOURCE") && pwd)/pycdirs.py"
    complete -o dirnames -C '_cdirs --complete "$COMP_LINE"' ${_CDIRS_CMD:-cdirs}
    [ "$_CDIRS_NO_PROMPT_COMMAND" ] || {
        #populate directory list. avoid clobbering other PROMPT_COMMANDs.
        grep "_cdirs --add-history" <<< "$PROMPT_COMMAND" >/dev/null || {
            PROMPT_COMMAND="$PROMPT_COMMAND"$'\n''(_cdirs --add-history "$(command pwd '$_CDIRS_RESOLVE_SYMLINKS' 2>/dev/null)" 2>/dev/null &);'
        }
    }
fi
