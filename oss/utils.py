#encoding=utf-8
import cPickle, commands, json, re, time

import psutil
import redis
# e_mail about
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
import smtplib

from api_requests import post_http
from etc.config import *


def get_date(time_stamp=int(time.time())):
    """:return 20171115"""
    return time.strftime("%Y%m%d", time.localtime(time_stamp))


def get_user_info():
    cache = get_cache()
    user_info = cache.get("kaola_user_info")
    if not user_info:
        data = {
            "auth": {
                    "passwordCredentials":{
                            "username": USER_NAME,
                            "password": PASSWORD,
                            },
                    "tenantName": TENANT_NAME
                    }
                }
        data = json.dumps(data)
        headers = {'content-type': 'application/json'}
        result = post_http(url=AUTH_URL, headers=headers, data=data)
        if result.status_code != 200:
            em = "get token error....."
            print em
            return
        token = result.json()['access']['token']['id']
        project_id = result.json()['access']["token"]['tenant']["id"]
        user_info =  {"token": token,
                      "project_id": project_id,
                      }
        msg = cPickle.dumps(user_info)
        cache.set("kaola_user_info", msg)
        cache.expire("kaola_user_info", 3600)
        return user_info
    user_info = cPickle.loads(user_info)
    return user_info


def get_cache():
    cache = redis.Redis(host=REDIS_SERVER, password=REDIS_PASSWORD, db=REDIS_TS_DB)
    if cache:
        return cache


def get_ts_time_len(ts_file):
    cmd = [TS_MET_CMD,
           "-i",
           "{0}".format(ts_file),
           "-show_entries",
           "format=duration",
           "-v",
           "quiet",
           "-of",
           "csv='p=0'",
           ]
    return exec_cmd(' '.join(cmd))


def exec_cmd(cmd_str):
    print "Running Command: [{0}]".format(cmd_str)
    result = commands.getstatusoutput(cmd_str)
    if result[0] != 0:
        em = "print get Duration error"
        print em
        return ()
    return result[1]


def find_procs_by_name(name):
    "Return a list of processes matching 'pid'."
    result = []
    for p in psutil.process_iter(attrs=["name", "exe", "cmdline"]):
        for cmd in p.info["cmdline"]:
            if name in cmd:
                result.append(p.pid)
    return result


class ConvertTsFileName(object):
    """
    传入ts文件名。获取各种数据。
    ts文件名格式：1513307165949_6_208000_01ws0000022.ts
        1513307165949：ts文件的生成时间（毫秒）
        6_208000：持续时间
        01ws0000022：文件的续号，自增+1
        .ts：扩展名，必须以ts结尾
    """
    def __init__(self, ts_file_name, digit=6):
        self.pat = re.compile(r'\d+')
        self.ts_lst = re.findall(self.pat, ts_file_name)
        if len(self.ts_lst) == 0:
            raise ValueError("Error <{0}>  ts name error".format(ts_file_name))
        # ts文件时长保留的小数点位数
        self.digit = digit

    # 时间戳是毫秒，除以1000
    @property
    def timestamp(self):
        if len(self.ts_lst[0]) > 10:
            return int(int(self.ts_lst[0]) / 1000.0)
        return int(int(self.ts_lst[0]))
    # 时间戳是毫秒，除以1000
    @property
    def timestamp_millisecond(self):
        return "%.3f" % (self.timestamp / 1000.0)

    # 获取文件的时区。`2017-12-13T15:42:28.846+08:00`
    @property
    def timestamp_tz(self):
        return time.strftime('%Y-%m-%dT%H:%M:%S.{0}+08:00'.format(self.timestamp_millisecond.split(".")[-1]),
                                                                  time.localtime(self.timestamp) )

    # ts文件的时长
    @property
    def ts_time_len(self):
        return "{0}.{1}".format(self.ts_lst[1], self.ts_lst[2][:self.digit])

    # ts文件的序号
    @property
    def ts_order_no(self):
        if len(self.ts_lst) < 5:
            return 0
        return int(self.ts_lst[-1])


def send_email(subject, content, receiver_email):
    """send mail to dst_email address"""
    try:
        #msg = MIMEText(content, 'plain', 'utf-8')
        msg = MIMEText(content,_subtype='html',_charset='utf-8')
        msg['From'] = _format_addr(from_email)
        msg['To'] = _format_addr(u'<%s>' % receiver_email)
        msg['Subject'] = Header(subject, 'utf-8').encode()

        server = smtplib.SMTP(SMTP_SERVER, 25)
        server.set_debuglevel(1)
        server.login(from_email, from_email_password)
        server.sendmail(from_email, [receiver_email], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        em = "send mail to <{0}> error. msg: {1}".format(receiver_email, e)
        print em
        return False

def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(),
                       addr.encode('utf-8') if isinstance(addr, unicode) else addr))
