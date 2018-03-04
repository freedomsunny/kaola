#encoding=utf-8
import time
import sys
sys.path.append('/root/kaola')
from _redis_op.redis_op import RedisOpreate
import re
from oss.utils import get_cache, ConvertTsFileName


class GetRedisTsData(object):
    @staticmethod
    def get_broadcast_data(channelID, stime, etime):
        cache = get_cache()
        s_time = ConvertTime(int(stime))
        e_time = ConvertTime(int(etime))
        s_index = RedisOpreate.binary_search_loop(channelID, s_time.to_time_stamp)
        e_index = RedisOpreate.binary_search_loop(channelID, e_time.to_time_stamp)
        data = cache.lrange(channelID, s_index, e_index)
        return data
        # ts_data = []
        # last = 0
        # for tsfile in data:
        #     ts_data_obj = ConvertTsFileName(ts_file_name=tsfile)
        #     if s_time.to_time_stamp <= ts_data_obj.timestamp <= e_time.to_time_stamp:
        #         if ts_data_obj.timestamp - last > 5:
        #             ts_data.append(tsfile)
        #     last = ts_data_obj.timestamp
        #
        # return ts_data


class ConvertTime(object):
    def __init__(self, date):
        """date is like this `20171018062800`"""
        date = str(date)
        self.year = date[:4]
        self.month = date[4:6]
        self.day = date[6:8]
        self.hour = date[8:10]
        self.minet = date[10:12]
        self.secend = date[12:]
        self.date = "{0}-{1}-{2} {3}:{4}:{5}".format(self.year,
                                                     self.month,
                                                     self.day,
                                                     self.hour,
                                                     self.minet,
                                                     self.secend)
    @property
    def to_time_stamp(self):
        return  int(time.mktime(time.strptime(self.date, '%Y-%m-%d %H:%M:%S')))


def get_date(time_stamp):
    """:return 20171115"""
    return time.strftime("%Y%m%d", time.localtime(time_stamp))



