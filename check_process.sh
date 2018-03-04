#!/bin/bash

oss_process=$(ps -aux | grep oss.py | grep -v grep | wc -l)
request_process=$(ps -aux | grep request_handle.py | grep -v grep | wc -l)

if [[ $oss_process -le 0 ]];then
  echo "starting oss.py........"
  python /root/kaola/oss/oss.py 2&> /dev/null &
  oss_pid=$(ps -aux | grep oss.py | grep -v grep | awk '{print $2}')
  echo "success with starting oss.py. pid is: $oss_pid"
fi


if [[ $request_process -le 0 ]];then
  echo "starting request_handle.py........"
  python /root/kaola/api/request_handle.py 2&> /dev/null &
  sleep 2
  request_process=$(ps -aux | grep request_handle.py | grep -v grep | awk '{print $2}')
  echo "success with starting request_handle.py. pids are:"
  echo "$request_process"
fi