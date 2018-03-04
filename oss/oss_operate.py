#encoding=utf-8
import time

from tomorrow import threads

from api_requests import get_http, post_http, put_http, delete_http
from etc.config import *
from utils import get_user_info, get_date


class OSSOperate(object):
    @staticmethod
    def delete_container(token, project_id, container):
        """删除容器"""
        headers = {"X-Auth-Token": token.strip()}
        url = OSS_URL + "AUTH_" + project_id + "/" + container
        ret = delete_http(url=url, headers=headers)
        if ret.status_code != 204:
            em = "delete container <{0}> error".format(container)
            print em
            return
        print "delete container <{0}> success".format(container)

    @staticmethod
    def create_container(token, project_id, container, public=True):
        """创建容器"""
        headers = {"X-Auth-Token": token.strip(), "X-Container-Read": ".r:*,.rlistings"}
        url = OSS_URL + "AUTH_" + project_id + "/" + container
        ret = put_http(url=url, headers=headers)
        if ret.status_code != 201:
            em = "create container <{0}> error...".format(container)
            print em
            return
        if public:
            # 更新容器为public
            ret = post_http(url=url, headers=headers)
            if ret.status_code != 204:
                em = "setting for container <{0}> to public error.".format(container)
                print em
                return
        print "create container <{0}> success".format(container)

    @staticmethod
    def list_containers(token, project_id):
        """得到所有容器"""
        headers = {"X-Auth-Token": token.strip()}
        url = OSS_URL + "AUTH_" + project_id + "?format=json"
        ret = get_http(url=url, headers=headers)
        print ret.status_code
        if ret.status_code != 200:
            em = "list containers error...."
            print em
            return
        return ret.json()

    @staticmethod
    def list_container_objs(token, project_id, container):
        """列出容器中的所有对象"""
        headers = {"X-Auth-Token": token.strip()}
        url = OSS_URL + "AUTH_" + project_id + "/" + container + "?format=json"
        ret = get_http(url=url, headers=headers)
        if ret.status_code != 200:
            em = "list container <{0}> error....".format(container)
            print em
            return
        return ret.json()

    @staticmethod
    @threads(10)
    def delete_container_objs(token, project_id, container, obj_file):
        """删除容器中的某个文件"""
        headers = {"X-Auth-Token": token.strip()}
        url = OSS_URL + "AUTH_" + project_id + "/" + container + "/" + obj_file
        ret = delete_http(url=url, headers=headers)
        if ret.status_code != 204:
            em = "delete container <{0}> file <{1}> error....".format(container, obj_file)
            print em
            return
        print "delete file <{0}> in container <{1}> success".format(obj_file, container)

    @staticmethod
    def upload_container_obj(token, project_id, container, obj_file, data):
        """上传文件到oss"""
        headers = {"X-Auth-Token": token.strip(), "Content-Type": ""}
        url = OSS_URL + "AUTH_" + project_id + "/" + container + "/" + obj_file
        ret = put_http(url=url, headers=headers, data=data)
        if ret.status_code != 201:
            em = "upload file <{0}> to container <{1}> error".format(obj_file, container)
            print em
            return
        em = "upload file <{0}> to container <{1}> success".format(obj_file, container)
        with open(LOG_FILE, "a+") as F:
            F.write(em)
        print em

    @staticmethod
    def delete_container_ndays_ago(token, project_id, delete_days_ago=7):
        """删除n天之前的容器以及文件"""
        # 获取所有容器
        containers = OSSOperate.list_containers(token, project_id)
        if not containers:
            return
        # n天前的时间戳
        time_days_ago = int(time.time()) - (delete_days_ago * 86400)
        # n天前的时间 e.g: 20171115
        date_days_ago = get_date(time_days_ago)
        for container in containers:
            container_name = container.get("name")
            if container_name.startswith("kolla"):
                # 得到容器创建的时间
                container_date = int(container_name[5:])
                # 容器创建小于n天，删除对象，再删除容器
                if int(date_days_ago) > container_date:
                    objs = OSSOperate.list_container_objs(token, project_id, container_name)
                    for obj in objs:
                        obj_file_name = obj.get("name")
                        OSSOperate.delete_container_objs(token, project_id, container_name, obj_file_name)
                    # 删除容器
                    OSSOperate.delete_container(token, project_id, container_name)

    @staticmethod
    def multi_process_del_obj_file(token, project_id, container):
        obj_files = OSSOperate.list_container_objs(token=token, project_id=project_id, container=container)
        for obj_file in obj_files:
            obj_file_name = obj_file.get("name")
            OSSOperate.delete_container_objs(token=token,
                                             project_id=project_id,
                                             container=container,
                                             obj_file=obj_file_name)


if __name__ == "__main__":
    user_info = get_user_info()
    # 创建新的容器，当天创建明天的容器
    tomorrow_date = int(time.time()) + 86400
    container_name = CONTAINER_PREFIX + get_date(tomorrow_date)
    OSSOperate.create_container(user_info["token"], user_info["project_id"], container_name)
    # 删除n天之前的容器
    OSSOperate.delete_container_ndays_ago(user_info["token"], user_info["project_id"])
