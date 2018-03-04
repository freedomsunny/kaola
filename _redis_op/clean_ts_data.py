#encoding=utf-8
import sys
sys.path.append('/root/kaola')
import time
from etc.config import *
from oss.utils import get_cache
from tomorrow import threads
from _redis_op.redis_op import RedisOpreate


class RedisCleanOpreate(object):
    cache = get_cache()

    @staticmethod
    def clean_all_data():
        """获取所有键"""
        keys = RedisOpreate.cache.keys()
        if not keys:
            print("not get any more keys")
            return
        # N天之前的时间戳
        Nday_timestamp = int(time.time()) - REDIS_TS_SAVE_DAY * 86400
        for key in keys:
            try:
                # 目前所有频道都为整数类型
                int(key)
                times = RedisOpreate.binary_search_loop(key, Nday_timestamp)
                if times:
                    RedisCleanOpreate.clean_data(key, times)
                    print("Starting clean key: <{0}> times: <{1}>".format(key, times))
            except ValueError:
                continue

    @staticmethod
    @threads(10)
    def clean_data(key, times):
        """从第一个元素依次删除，删除`times`次"""
        for i in range(times):
            RedisOpreate.cache.lpop(key)
        em = "remove element from key <{0}> success. count: <{1}>".format(key, times)
        print(em)


if __name__ == '__main__':
    RedisCleanOpreate.clean_all_data()
