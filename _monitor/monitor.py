#encoding=utf-8
import sys
sys.path.append("/root/kaola")
import json
import time
import os
import shutil
import psutil


from _monitor.send_msg import SendMsg
from tomorrow import threads
from oss.utils import ConvertTsFileName, get_cache, exec_cmd, send_email, find_procs_by_name
from etc.config import *
from oss.api_requests import *


class Monitor(object):
    def __init__(self):
        self.cache = get_cache()
        self.msg_obj = SendMsg()

    def check_radios(self):
        """检测所有电台推流时间间隔
        :return 异常电台的拉取源流"""
        radios_obj = GetRadios()
        send_msg_info = self.cache.lrange("send_msg_radios", 0, -1)
        invalid_radios = []
        for data in radios_obj.radios_data:
            radio = str(data.get("id"))
            ts_file = self.cache.lrange(radio, -1, -1)
            detail = u"频道<{0}>已超过{1}秒未更新，对应节点：<node{2}>\n请及时检查".format(radio,
                                                                                      MONITOR_RADIOS_FAILED_TIME,
                                                                                      int(radio) % 8
                                                                                     )
            task = u"srs频道不更新"
            if not ts_file:
                # 只发送一次（一天间隔）
                if radio not in send_msg_info:
                    self.msg_obj.send_msg(detail=detail, task=task)
                    self.cache.rpush("send_msg_radios", radio)
                invalid_radios.append(data)
                continue

            ts_fileobj = ConvertTsFileName(ts_file[0])
            if time.time() - ts_fileobj.timestamp > MONITOR_RADIOS_FAILED_TIME:
                if radio not in send_msg_info:
                    self.msg_obj.send_msg(detail=detail, task=task)
                    self.cache.rpush("send_msg_radios", radio)
                invalid_radios.append(data)
                continue
        return invalid_radios


class GetRadios(object):
    def __init__(self, radios_api=RADIOS_API):
        self.radios_api = radios_api

    @property
    def radios_data(self):
        """频道的所有数据，包括拉取源的url"""
        api_result = get_http(url=self.radios_api)
        if api_result.status_code != 200:
            print("Error request radios API <{0}> error".format(self.radios_api))
            return []
        datas = json.loads(api_result.text)

        return datas.get('result').get("dataList")

    @property
    def radios(self):
        """获取所有频道"""
        result = []
        for radio in self.radios_data:
            result.append(radio.get("id"))
        return result


def check_radio_source(radios):
    """检查源流是否可用，根据http返回状态码来确定
    radios: {"radio_id": "pull_url"} """
    result = []
    for radio in radios:
        url = 'http://127.0.0.1:8040/live/{0}/index.m3u8'.format(radio)
        http_ret = get_http(url=url)
        if http_ret.status_code == 404:
            result.append(radios.get(radio))
    # 发送邮件
    if result:
        for receive_user in RECEIVE_USERS:
            sub_ject = u"srs无效源"
            content = '</br>'.join(result)
            send_email(subject=sub_ject, content=content, receiver_email=receive_user)


def spwan_radio_process(invalid_radios):
    # 每次启动前清除所有推流进程
    id_run_process = find_procs_by_name("/usr/local/kala/id-run.sh")
    ffmpeg_process = find_procs_by_name("/usr/local/kala/ffmpeg")
    all_process = id_run_process + ffmpeg_process
    for pid in all_process:
        pid_obj = psutil.Process(pid=pid)
        pid_obj.kill()
    # 清除频道所有目录
    os.popen("rm -rf /data/srs/live/*")
    radio_id = 1
    radios = {}
    # 启动拉流进程
    for invalid_radio in invalid_radios:
        for pull_url in invalid_radio.get("pullUrl"):
            cmds = ["nohup",
                    "/usr/local/kala/id-run.sh",
                    "127.0.0.1:1940",
                    "{0}".format(radio_id),
                    "'{0}'".format(pull_url),
                    "&"
                    ]
            os.popen(' '.join(cmds))
            radios[radio_id] = pull_url
            radio_id += 1
    return radios


if __name__ == '__main__':
    # while True:
    #     obj = Monitor()
    #     obj.check_radios()
    #     time.sleep(MONITOR_RADIOS_INTERVAL)
    obj = Monitor()
    invalid_radios = obj.check_radios()
    spwan_radio_process(invalid_radios)
    for invalid_radio in invalid_radios:
        print invalid_radio
