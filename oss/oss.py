#encoding=utf-8
import time

import inotify.adapters
from tomorrow import threads

from etc.config import *
from oss_operate import OSSOperate
from utils import get_cache, get_user_info, find_procs_by_name, \
    get_ts_time_len, ConvertTsFileName


def get_new_ts(inotify_handle):
    cache = get_cache()
    for event in inotify_handle.event_gen():
        if event is not None:
            (header, type_names, watch_path, filename) = event
            if filename.endswith('.ts') and 'IN_MOVED_TO' == type_names[0]:
                container = time.strftime("{0}%Y%m%d".format(CONTAINER_PREFIX), time.localtime())
                ts_file = "%s/%s" % (watch_path.decode('utf-8'), filename.decode('utf-8'))
                channel = ts_file.split('/')[-2]
                ts_name = ts_file.split('/')[-1].split("-")[0]
                user_info = get_user_info()
                # 获取Ts文件的播放时长
                result = get_ts_time_len(ts_file)
                if not result:
                    print "get ts time len error. ts: <{0}>".format(ts_file)
                    continue
                # 获取频道的最后一个值，用来确定序号
                channel_last = cache.lrange(channel, -1, -1)
                # ts文件的序号
                ts_order_no = 0
                if channel_last:
                    ts_obj = ConvertTsFileName(channel_last[0])
                    ts_order_no = ts_obj.ts_order_no
                    ts_order_no += 1
                new_tsname = "{0}_{1}_{2}_01ws{3}.ts".format(ts_name,
                                                             result.split(".")[0],
                                                             result.split(".")[1],
                                                             str(ts_order_no).zfill(6)
                                                             )
                obj_file = channel + "/" + new_tsname
                cache.rpush(channel, new_tsname)
                upload_ts2oss(user_info=user_info,
                              container=container,
                              obj_file=obj_file,
                              ts_file=ts_file)


@threads(70)
def upload_ts2oss(user_info, container, obj_file, ts_file):
    with open(ts_file, "rb") as F:
        OSSOperate.upload_container_obj(token=user_info["token"],
                                        project_id=user_info["project_id"],
                                        container=container,
                                        obj_file=obj_file,
                                        data=F.read(),
                                        )


if __name__ == "__main__":
    result = find_procs_by_name("oss.py")
    if len(result) > 1:
        em = "process is already running with pid: {0}".format(result)
        print em
        exit(1)
    for monitor_dir in MONITOR_TS_DIRS:
        i = inotify.adapters.InotifyTree(monitor_dir)
        get_new_ts(i)
