#encoding=utf-8
import json

from etc.config import *
from oss.api_requests import *


class SendMsg(object):
    """发送报警信息"""
    def __init__(self, open_id=OPEN_ID):
        self.open_id = open_id

    def send_msg(self, task, detail, expire_time="2017-06-17"):
        """发送至微信报警"""
        req_data = {"open_id": self.open_id,
                    "task": task,
                    "detail": detail,
                    "expire_time": expire_time}
        headers = {"Content-Type": "application/json"}
        req_data = json.dumps(req_data)
        result = post_http(url=SEND_MSG_API, data=req_data, headers=headers)
        if result.json().get("code") != 0:
            print "Error send msg error to open id: <{0}>".format(self.open_id)
