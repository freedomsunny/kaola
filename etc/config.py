#!encoding=utf-8

USER_NAME = ""
PASSWORD = ""
AUTH_URL = ""
TENANT_NAME = ""
OSS_URL = ""
MONITOR_TS_DIRS = ["/data/srs/live"]
CONTAINER_PREFIX = 'kolla'
TS_PREFIX  = "http://tspb.x.l.kaolafm.net:8080/v1/AUTH_f6057bb00d2c45dda73f07848bab3642/kolla"
# 获取ts元数据命令
TS_MET_CMD = '/usr/bin/ffprobe'
##### redis #######
# redis元数据保存时间(天)
REDIS_TS_SAVE_DAY = 7
REDIS_SERVER = ""
REDIS_PASSWORD = ""
REDIS_TS_DB = 0


# log file
LOG_FILE = '/var/log/kaola_upload.log'


########## 监控相关
# 频道监控间隔 秒
MONITOR_RADIOS_INTERVAL = 300
# 判定频道失效的时间 秒
MONITOR_RADIOS_FAILED_TIME = 600
# 获取所有电台的API
RADIOS_API = 'http://api.kaolafm.com/api/v4/broadcast/newall'
# 发送报警的API
SEND_MSG_API = 'http://alert.xiangcloud.com.cn:8902/send_tem_msg'
# 发送消息的对象
OPEN_ID = ""

###### 发送邮件相关
SMTP_SERVER = 'smtp.xiangcloud.com.cn'
from_email = ""
from_email_password = ""
# 发送不可用源时的接收人
RECEIVE_USERS = ["1806832@qq.com"]

