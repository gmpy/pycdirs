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
            [ -d "${line#*\|}" ] && echo "${line%\|*}"
        done < "$labelfile"
        return 0
    }

    _cdirs_dirs() {
        [ -f "$histfile" ] || return

        local line
        while read line; do
            # only count directories
            if [ -d "${line%%\|*}" ]; then
                [ -n "$only_dir" ] && echo "${line%%\|*}" || echo "${line}"
            fi
        done < "$histfile"
        return 0
    }

    _cdirs_options() {
        echo "-h -s -l -d --help --set-label --list-label --del-label --list-history"
    }

    _cdirs_complete_check() {
        local key dir file

        key="$@"
        [ -d "$key" -o "${key:0:1}" = '.' -o "${key:0:1}" = '/' -o "${key:0:1}" = "~" ] && return 1
        [ "${key:0:1}" = '-' -o -z "${key}" ] && return 0

        dir="$(\dirname $key)"
        file="$(\basename $key)"
        [ -d "${dir}" -a "${dir}" != '.' ] && return 1
        \ls $dir 2>/dev/null | \grep -q "$file" 2>/dev/null && return 1
        return 0
    }

    _cdirs_complete() {
        shift

        # should complete by cdirs?
        _cdirs_complete_check "$1" || return

        case "$1" in
            ,*) _cdirs_labels;;
            -*) _cdirs_options;;
        esac
    }

    _cdirs_add_history() {
        shift

        # $HOME and / aren't worth matching
        [ "$*" = "$HOME" -o "$*" = '/' ] && return

        # maintain the history file
        local tempfile="$histfile.$RANDOM"
        local score="9000"
        _cdirs_dirs | \awk -v path="$*" -v now="$(\date +%s)" -v score=$score -F"|" '
            BEGIN {
                rank[path] = 1
                time[path] = now
            }
            $2 >= 1 {
                # drop rank below 1
                if ( $1 == path ) {
                    rank[$1] = $2 + 1
                    time[$1] = now
                } else {
                    rank[$1] = $2
                    time[$1] = $3
                }
                count += $2
            }
            END {
                if ( count > score ) {
                    # aging
                    for ( x in rank ) print x "|" 0.99*rank[x] "|" time[x]
                }  else for (x in rank ) print x "|" rank[x] "|" time[x]
            }
        ' 2>/dev/null >| "$tempfile"
        # do our best to avoid clobbering the histfile in a race condition.
        if [ $? -ne 0 -a -f "$histfile" ]; then
            \env rm -f "$tempfile"
        else
            \env mv -f "$tempfile" "$histfile" || \env rm -f "$tempfile"
        fi
    }

    _cdirs_jump() {
        local cd="${@:-${HOME}}"
        if [ -d "$cd" -o "${cd}" = '-' -o "${cd}" = '~' ]; then
            builtin cd "$cd"
        elif [ "${cd:0:1}" = '.' -o "${cd:0:1}" = '/' -o "${cd:0:1}" = '~' ]; then
            [ -d "$(\dirname ${cd})" ] && cd="$(\dirname ${cd})"
            builtin cd "$cd"
        elif [ -f "$cd" ]; then
            builtin cd "$(\dirname ${cd})"
        else
            cd="$(${_CDIRS_PY_PATH} "$cd")"
            [ "$?" -eq 0 ] && builtin cd "$cd" || echo "$cd"
        fi
    }

    _cdirs_py() {
        case "$1" in
            # It's faster to using script to complete and add history
            --complete) _cdirs_complete "$@";;
            --add-history) _cdirs_add_history "$@";;
            -) _cdirs_jump "$@";;
            -*|,,) ${_CDIRS_PY_PATH} $@;;
            *) _cdirs_jump "$@";;
        esac
    }

    if [ -x "$_CDIRS_PY_PATH" ]; then
        _cdirs_py "$@"
    else
        echo "not found or not executable: $_CDIRS_PY_PATH" && return 1
    fi
}

alias ${_CDIRS_CMD:-cdirs}='_cdirs 2>&1'

if type compctl >/dev/null 2>&1; then
    # zsh
    _CDIRS_PY_PATH="$(builtin cd $(dirname "$0") && pwd)/pycdirs.py"
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
    # todo
    #_cdirs_zsh_tab_completion() {
    #    # tab completion
    #    local compl
    #    read -l compl
    #    reply=(${(f)"$(_cdirs --complete "$compl")"})
    #}
    #compctl -U -K _cdirs_zsh_tab_completion _cdirs
elif type complete >/dev/null 2>&1; then
    # bash
    _CDIRS_PY_PATH="$(builtin cd $(dirname "$BASH_SOURCE") && pwd)/pycdirs.py"
    _cdirs_bash_tab_completion() {
        local cur="${COMP_WORDS[COMP_CWORD]}"
        local out="$(_cdirs --complete "${cur}")"
        COMPREPLY=($(compgen -W "${out}" -- "${cur}"))
    }
    complete -o dirnames -F _cdirs_bash_tab_completion ${_CDIRS_CMD:-cdirs}
    [ "$_CDIRS_NO_PROMPT_COMMAND" ] || {
        #populate directory list. avoid clobbering other PROMPT_COMMANDs.
        grep "_cdirs --add-history" <<< "$PROMPT_COMMAND" >/dev/null || {
            PROMPT_COMMAND="$PROMPT_COMMAND"$'\n''(_cdirs --add-history "$(command pwd '$_CDIRS_RESOLVE_SYMLINKS' 2>/dev/null)" 2>/dev/null &);'
        }
    }
fi
