#encoding=utf-8
import sys
sys.path.append('/root/kaola')
from oss.utils import get_cache, ConvertTsFileName


class RedisOpreate(object):
    cache = get_cache()

    @staticmethod
    def binary_search_loop(key, value):
        """从指定建中获取指定值"""
        key_len = RedisOpreate.cache.llen(key)
        low, high = 0, key_len - 1
        mid = 0
        while low <= high:
            mid = (low + high) // 2
            ts_file_obj = ConvertTsFileName(RedisOpreate.cache.lrange(key, mid, mid)[0])
            if ts_file_obj.timestamp < value:
                low = mid + 1
            elif ts_file_obj.timestamp > value:
                high = mid - 1
            else:
                return mid
        return mid
