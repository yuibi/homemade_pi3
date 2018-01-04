#!/bin/bash

pid=$$
wkdir='/var/tmp'
playerurl=http://radiko.jp/apps/js/flash/myplayer-release.swf
playerfile="${wkdir}/player.swf"
keyfile="${wkdir}/authkey.png"
auth1_fms="${wkdir}/auth1_fms_${pid}"
auth2_fms="${wkdir}/auth2_fms_${pid}"
date=`date +%Y%m%d_%H%M`
stream_url=""
url_parts=""

# Usage
show_usage() {
    echo 'Usage:'
    echo ' RECORD MODE' 1>&2
    echo "   `basename $0` [-d out_dir] [-f file_name]" 1>&2
    echo '          [-t rec_minute] [-s Starting_position] channel' 1>&2
    echo '           -d  Default out_dir = $HOME' 1>&2
    echo '                  a/b/c = $HOME/a/b/c' 1>&2
    echo '                 /a/b/c = /a/b/c' 1>&2
    echo '                ./a/b/c = $PWD/a/b/c' 1>&2
    echo '           -f  Default file_name = channel_YYYYMMDD_HHMM_PID' 1>&2
    echo '           -t  Default rec_minute = 1' 1>&2
    echo '               60 = 1 hour, 0 = go on recording until stopped(control-C)' 1>&2
    echo '           -s  Default starting_position = 00:00:00' 1>&2
    echo ' PLAY MODE' 1>&2
    echo "   `basename $0` -p [-t play_minute] channel" 1>&2
    echo '           -p  Plya mode. No recording.' 1>&2
    echo '           -t  Default play_minute = 0' 1>&2
    echo '               60 = 1 hour, 0 = go on recording until stopped(control-C)' 1>&2
}


# authorize
authorize() {
    #
    # get player
    #
    if [ ! -f ${playerfile} ]; then
        wget -q -O ${playerfile} ${playerurl}

        if [ $? -ne 0 ]; then
            echo "[stop] failed get player (${playerfile})" 1>&2 ; exit 1
        fi
    fi

    #
    # get keydata (need swftool)
    #
    if [ ! -f ${keyfile} ]; then
        swfextract -b 12 ${playerfile} -o ${keyfile}

        if [ ! -f ${keyfile} ]; then
            echo "[stop] failed get keydata (${keyfile})" 1>&2 ; exit 1
        fi
    fi

    #
    # access auth1_fms
    #
    wget -q \
        --header="pragma: no-cache" \
        --header="X-Radiko-App: pc_ts" \
        --header="X-Radiko-App-Version: 4.0.0" \
        --header="X-Radiko-User: test-stream" \
        --header="X-Radiko-Device: pc" \
        --post-data='\r\n' \
        --no-check-certificate \
        --save-headers \
        -O ${auth1_fms} \
        https://radiko.jp/v2/api/auth1_fms

    if [ $? -ne 0 ]; then
        echo "[stop] failed auth1 process (${auth1_fms})" 1>&2 ; exit 1
    fi

    #
    # get partial key
    #
    authtoken=`perl -ne 'print $1 if(/x-radiko-authtoken: ([\w-]+)/i)' ${auth1_fms}`
    offset=`perl -ne 'print $1 if(/x-radiko-keyoffset: (\d+)/i)' ${auth1_fms}`
    length=`perl -ne 'print $1 if(/x-radiko-keylength: (\d+)/i)' ${auth1_fms}`
    partialkey=`dd if=${keyfile} bs=1 skip=${offset} count=${length} 2> /dev/null | base64`

    #echo "authtoken: ${authtoken} 1>&2
    #echo "offset: ${offset} 1>&2
    #echo "length: ${length} 1>&2
    #echo "partialkey: ${partialkey}" 1>&2

    rm -f ${auth1_fms}

    #
    # access auth2_fms
    #
    wget -q \
        --header="pragma: no-cache" \
        --header="X-Radiko-App: pc_ts" \
        --header="X-Radiko-App-Version: 4.0.0" \
        --header="X-Radiko-User: test-stream" \
        --header="X-Radiko-Device: pc" \
        --header="X-Radiko-Authtoken: ${authtoken}" \
        --header="X-Radiko-Partialkey: ${partialkey}" \
        --post-data='\r\n' \
        --no-check-certificate \
        -O ${auth2_fms} \
        https://radiko.jp/v2/api/auth2_fms

    if [ $? -ne 0 -o ! -f ${auth2_fms} ]; then
        echo "[stop] failed auth2 process (${auth2_fms})" 1>&2 ; exit 1
    fi

    #echo "authentication success" 1>&2

    areaid=`perl -ne 'print $1 if(/^([^,]+),/i)' ${auth2_fms}`
    #echo "areaid: ${areaid}" 1>&2
    rm -f ${auth2_fms}

    #
    # get stream-url
    #
    wget -q -O ${ch_xml} \
        "http://radiko.jp/v2/station/stream/${channel}.xml"

    if [ $? -ne 0 -o ! -f ${ch_xml} ]; then
        echo "[stop] failed stream-url process (channel=${channel})"
        rm -f ${ch_xml} ; show_usage ; exit 1
    fi

    stream_url=`echo "cat /url/item[1]/text()" | \
            xmllint --shell ${ch_xml} | tail -2 | head -1`
    url_parts=(`echo ${stream_url} | \
            perl -pe 's!^(.*)://(.*?)/(.*)/(.*?)$/!$1://$2 $3 $4!'`)
    rm -f ${ch_xml}

}


# Record
record() {
    # rtmpdump
    rtmpdump -r ${url_parts[0]} \
        --app ${url_parts[1]} \
        --playpath ${url_parts[2]} \
        -W ${playerurl} \
        -C S:"" -C S:"" -C S:"" -C S:${authtoken} \
        --live \
        --stop ${duration} \
        --flv "${wkdir}/${tempname}.flv"

    avconv -ss ${starting} -i "${wkdir}/${tempname}.flv" \
        -acodec copy "${wkdir}/${tempname}.m4a" && \
        rm -f "${wkdir}/${tempname}.flv"

    mv -b "${wkdir}/${tempname}.m4a" "${outdir}/${filename}.m4a"

    if [ $? -ne 0 ]; then
        echo "[stop] failed move file (${wkdir}/${tempname}.m4a to \
            ${outdir}/${filename}.m4a)" 1>&2 ; exit 1
    fi
}


# Play
play() {
    # rtmpdump
    rtmpdump -r ${url_parts[0]} \
        --app ${url_parts[1]} \
        --playpath ${url_parts[2]} \
        -W $playerurl \
        -C S:"" -C S:"" -C S:"" -C S:$authtoken \
        --live \
        --stop ${duration} | \
        mplayer -
}


# debug
debug() {
    echo "-p : ${OPTION_p}"
    echo "-d : ${OPTION_d}    value: \"${VALUE_d}\""
    echo "-f : ${OPTION_f}    value: \"${VALUE_f}\""
    echo "-t : ${OPTION_t}    value: \"${VALUE_t}\""
    echo "-s : ${OPTION_s}    value: \"${VALUE_s}\""
    echo ''
    echo "channel : \"${channel}\""
    echo "outdir  : \"${outdir}\""
    echo "filename: \"${filename}\""
    echo "duration: \"${duration}\""
    echo "starting: \"${starting}\""
    echo ''
}


# Get Option
while getopts pd:f:t:s: OPTION
do
    case $OPTION in
        p ) OPTION_p=true
            ;;
        d ) OPTION_d=true
            VALUE_d="$OPTARG"
            ;;
        f ) OPTION_f=ture
            VALUE_f="$OPTARG"
            ;;
        t ) OPTION_t=true
            VALUE_t="$OPTARG"
            if ! expr "${VALUE_t}" : '[0-9]*' > /dev/null ; then
                show_usage ; exit 1
            fi
            ;;
        s ) OPTION_s=ture
            VALUE_s="$OPTARG"
            ;;
        * ) show_usage ; exit 1 ;;
    esac
done

# Get Channel
shift $(($OPTIND - 1))
if [ $# -ne 1 ]; then
    show_usage ; exit 1
fi
channel=$1

ch_xml="${wkdir}/${channel}${pid}.xml"

#
# RECORD Mode
#
if [ ! "${OPTION_p}" ]; then
    # Get Directory
    if [ ! "$OPTION_d" ]; then
        cd ${HOME}
    else
        if echo ${VALUE_d}|grep -q -v -e '^./\|^/'; then
            mkdir -p "${HOME}/${VALUE_d}"
            if [ $? -ne 0 ]; then
                echo "[stop] failed make directory (${HOME}/${VALUE_d})" 1>&2 ; exit 1
            fi
            cd "${HOME}/${VALUE_d}"
        else
            mkdir -p ${VALUE_d}
            if [ $? -ne 0 ]; then
                echo "[stop] failed make directory (${VALUE_d})" 1>&2 ; exit 1
            fi
            cd ${VALUE_d}
        fi
    fi
    outdir=${PWD}

    # Get File Name
    filename=${VALUE_f:=${channel}_${date}_${pid}}
    tempname=${channel}_${pid}

    # Get Minute
    min=${VALUE_t:=1}
    duration=`expr ${min} \* 60`

    # Get Starting Position
    starting=${VALUE_s:='00:00:00'}

#    debug
    authorize && record

#
# PLAY Mode
#
else
    # Get Minute
    duration=`expr ${VALUE_t:=0} \* 60`

#    debug
    authorize && play

fi
