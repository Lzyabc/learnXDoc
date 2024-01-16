# 从命令行中获取文件名
# 解析配置文件
# 逐个创建容器

import logging
import getopt
import sys
import json
import subprocess
import os
from nsenter import Namespace

import docker
import socket
from contextlib import closing
from map import *

import shutil

from util import nginx_util

client = docker.from_env()
api_client = docker.APIClient()

default_config = {
    "constrain": {
        "cpu_quota": int(1*100000),
        "mem_limit": "2g",
        "memswap_limit": "4g"
    },
    "network": {
        "network_upload_rate": "4096",
        "network_download_rate": "4096"
    },
    "export_port_map": {
        "8081/tcp": "",
        "8080/tcp": ""
    }
}

# workdir = "/root/data"
# basicdir = "/root/data/project"
containerdir = "/home/coder/project"

def create_dir_not_exist(path):
    if not os.path.exists(path):
        shutil.copytree(basicdir, path)
        os.system("chown -R 1000:1000 " + path)

def get_free_port():
    """ Get free port"""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

class NetworkInfo:
    def __init__(self) -> None:
        process = subprocess.run("ip -j a".split(), 
                            capture_output=True, text=True)
        self.networkdevices = json.loads(process.stdout)
        self.deviceMap = {}
        for deviceInfo in self.networkdevices:
            deviceIndex = deviceInfo["ifindex"]
            self.deviceMap[deviceIndex] = deviceInfo

    def get_virtual_network_interface_name(self,deviceIndex):
        if not self.deviceMap.__contains__(deviceIndex):
            return False, ""
        if not self.deviceMap[deviceIndex].__contains__("ifname"):
            return False, ""
        return True, self.deviceMap[deviceIndex]["ifname"]

def get_peer_ifindex(SandboxKey):
    try:
        with Namespace(SandboxKey, 'net') as n:
            pipeline = os.popen("ethtool -S eth0")
            statistics = pipeline.read()
            statisticsList = statistics.split("\n")
            for line in statisticsList:
                if "peer_ifindex" in line:
                    peer_ifindex = line.replace(" ", "").split(":")[1]
                    return True, int(peer_ifindex)
    except:
        pass
    return False, None

def get_network_interface_name(sandboxKey):
    # print("sandboxKey",sandboxKey)
    ok, peer_ifindex = get_peer_ifindex(sandboxKey)
    if not ok:
        return False, ""
    networkInfo = NetworkInfo()
    ok, interfaceName = networkInfo.get_virtual_network_interface_name(
        peer_ifindex)
    return ok, interfaceName

def set_network_bps(networkInterfaceName, uploadRate, downloadRate):
    # print("set_network_bps")
    cmd = "wondershaper %s %s %s" % (
        networkInterfaceName, uploadRate, downloadRate)
    try:
        res = subprocess.Popen(cmd.split())
        res.wait()
        ok = False
        if res.returncode == 0:
            ok = True
    except Exception as err:
        import logging
        logging.exception(err)
        ok = False
    return ok

class Container:
    def __init__(self, name, info) -> None:
        self.name = name
        self.info = info
        self.info["status"] = "unknown"
        self.hostdir = os.path.join(workdir, name)
        create_dir_not_exist(self.hostdir)

    def create(self):
        """create: 创建容器
        """
        image = "lucaszy/webide:latest"
        # cmd = 'bash -c "%s && %s"' % ("export PASSWORD=123456",
        #                               "code-server --bind-addr 0.0.0.0:8081")
        cmd = "bash -c 'export PASSWORD=%s && code-server --bind-addr 0.0.0.0:8080'" % (self.info["password"])
        print("cmd", cmd)
        # cmd = "\"bash -c \'export PASSWORD='%s' && code-server --bind-addr 0.0.0.0:8081\'\"" % (self.info["password"])
        constrain = {}
        for key in default_config["constrain"]:
            constrain[key] = default_config["constrain"][key]

        environment = [
            "PASSWORD={password}".format(password=self.info["password"])
        ]

        port_map = {}
        for port in default_config["export_port_map"]:
            port_map[port] = get_free_port()

        volumes={self.hostdir: {'bind': containerdir, 'mode': 'rw'}}
        try:
            container: Container = client.containers.run(image=image, command=cmd, environment=environment, name=self.name, ports=port_map,
                                                         volumes=volumes, detach=True, tty=True, **constrain)
            print("success create the container")
            self.info["port_map"] = port_map
            self.info["status"] = "running"
            self.info["container_id"] = container.id
            # self.constrain_container()
            return True, container.id
        except Exception as err:
            print("Error occurs when creating the container", err)
            return False, err

    def constrain_container(self):
        """constrain_container: 调用RPC接口限制容器带宽
        """
        apiClient = docker.APIClient()
        network_settings = apiClient.inspect_container(self.info.get("container_id"))["NetworkSettings"]
        sandbox_key = network_settings["SandboxKey"]
        ok, interfaceName = get_network_interface_name(sandbox_key)
        if not ok:
            return False
        upload_rate = default_config["network"]["network_upload_rate"]
        download_rate = default_config["network"]["network_download_rate"]
        ok = set_network_bps(interfaceName,upload_rate, download_rate)
        return ok
    
    def change_state(self, state, timeout=10):
        container:Container =client.containers.get(self.name)
        if not container:
            return True
        try:
            if state == "stop":
                container.stop(timeout=timeout)
            elif state == "start":
                container.start()
                self.constrain_container()
            elif state == "remove":
                container.remove(force=True)
            else:
                pass
            self.info["status"] = state
        except Exception as err:
            print(err)
            return False
        return True

    def get_status(self):
        return self.info


class Manager:
    """Manager: 输入文件名，解析文件得到一组container的配置
               并逐个启动容器，将容器状态记录到               
    """

    def __init__(self, cmd, input, output, env) -> None:
        self.cmd = cmd
        self.input = input
        self.output = output
        self.env = env
        self.container_list = {}
        self.container_status = {}
        self.parse()

    def parse(self):
        """parse:解析文件，记录到container_list中
        """
        content = "{}"
        with open(self.input, "r") as f:
            content = f.read()
        students_info = json.loads(content)
        for s in students_info:
            c = Container(s, students_info[s])
            self.container_list[s] = c

    def run(self):
        for c_name in self.container_list:
            c = self.container_list[c_name]
            if self.cmd == "create":
                c.create()
            else:
                c.change_state(cmd)
            self.container_status[c_name] = c.get_status()
        self.save_status()

    def save_status(self):
        with open(self.output, "w") as f:
            f.write(json.dumps(self.container_status))
        if self.cmd == "create":
            nginx_util.write_nginx_config(self.env, self.container_status)


def parse_args(argv):
    args = {}
    try:
        opts, _ = getopt.getopt(argv, "hc:i:o:d:n:", ["cmd", "input", "output", "domain", "nginx"])
    except getopt.GetoptError:
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-c", "--cmd"):
            args['cmd'] = arg
        elif opt in ("-i", "--input"):
            args['input'] = arg
        elif opt in ("-o", "--output"):
            args['output'] = arg
        elif opt in ("-d", "--domain"):
            args['domain'] = arg
        elif opt in ("-n", "--nginx"):
            args['nginx'] = arg
        else:
            pass
    return args


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    cmd = args.get("cmd")
    config_file = args.get("input")
    status_file = args.get("output")
    env = {}
    env["nginx"] = args.get("nginx") if args.get("nginx") != None else "config/nginx.conf"
    env["domain"] = args.get("domain") if args.get("domain") != None else "course"
    m = Manager(cmd, config_file, status_file, env)
    m.run()
