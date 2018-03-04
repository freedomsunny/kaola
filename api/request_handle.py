#encoding=utf-8
import sys
sys.path.append("/root/kaola")
from etc.config import *

import tornado.web
from tornado.netutil import bind_sockets

from api.plugins import GetRedisTsData, get_date, ConvertTsFileName


class Base(tornado.web.RequestHandler):
    def __init__(self, application, request, **kwargs):
        super(Base, self).__init__(application, request, **kwargs)
        if request.method != 'OPTIONS':
            self.context = {'start': int(self.get_argument("start", 0)),
                            'length': int(self.get_argument("length", 10000))}

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
        self.set_header("Access-Control-Allow-Headers", "X-Auth-Token, Content-type")
        self.set_header("Content-Type", "application/json")
        self.set_header("Content-Type", "application/vnd.apple.mpegurl")

    def options(self, *args, **kwargs):
        self.finish()


class GetBroadcast(Base):
    def get(self):
        # 频道ID
        broadcastId = self.get_argument("broadcastId", "")
        stime = self.get_argument("stime", "")
        etime = self.get_argument("etime", "")

        result = GetRedisTsData.get_broadcast_data(broadcastId, stime, etime)
        if not result:
            em = "can not get broadcastId: <{0}>  start time: <{1} end time <{2}>".format(broadcastId, stime, etime)
            with open(LOG_FILE, "a+") as F:
                F.write(em)
            print em
            self.set_status(404)
        # 处理结果，每个列表元素前面加上 `#EXTINF:10.008,` 字符串
        result_lst = []
        # 单个文件播放最大长度
        longest_time = 0
        first_time = None
        first_sequence = None
        for ts_file in result:
            ts_file_obj = ConvertTsFileName(ts_file_name=ts_file, digit=6)
            # 第一个文件的时区信息
            if not first_time:
                first_time = ts_file_obj.timestamp_tz
            if not first_sequence:
                first_sequence = ts_file_obj.ts_order_no
            prefix = "#EXTINF:%s," % ts_file_obj.ts_time_len
            result_lst.append(prefix)
            ts_date = get_date(ts_file_obj.timestamp)
            # 对象存储的完整url
            oss_url = TS_PREFIX + ts_date + "/" + str(broadcastId) + "/" + ts_file
            result_lst.append(oss_url)
            if float(ts_file_obj.ts_time_len) > longest_time:
                longest_time = float(ts_file_obj.ts_time_len)
        return_heade = ["#EXTM3U",
                        "#EXT-X-VERSION:3",
                        "#EXT-X-MEDIA-SEQUENCE:{0}".format(first_sequence),
                        "#EXT-X-ALLOW-CACHE:YES",
                        "#EXT-X-PROGRAM-DATE-TIME:%s" % first_time,
                        "#EXT-X-TARGETDURATION:{0}".format(int(longest_time) + 1),
                        "",
                        "",]
        return_end = ["#EXT-X-ENDLIST", ""]

        result = return_heade + result_lst + return_end
        result_str = "\n".join(result)
        self.write(result_str)


application = tornado.web.Application([
    (r"/broadcast", GetBroadcast),
    (r"/play3.php", GetBroadcast),
    (r"/play.m3u8", GetBroadcast),
    ])

if __name__ == "__main__":
    sockets = bind_sockets(8888, "0.0.0.0")
    tornado.process.fork_processes(0)  # start multi sub process as cpu numbers
    http_server = tornado.httpserver.HTTPServer(application, xheaders=True)
    http_server.add_sockets(sockets)
    tornado.ioloop.IOLoop.instance().start()

