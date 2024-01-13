from copy import Error, error
import docker
import socket
from contextlib import closing

from docker.client import DockerClient
from docker.models.containers import Container
from docker.types import containers
from dockerproxy.util import disk_util, cgroup_util
'''
本代码先不考虑容错
'''
def getFreePort():
    """Get free port"""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

class DockerProxy:
    def __init__(self):
        self.client = docker.from_env()
        # print("init")
    def get_from_dict(self, d:dict, key):
        if d.__contains__(key):
            return d[key]
        return None
        
    def run_container(self, imageName, containerName, portMap=None, initCmd=None, detach=True, tty=True, resourceConstrain:dict={}):
        '''
        resourceConstrain可以限制容器的cpu，memory，disk占用，以及磁盘的读写速度限制
        resourceConstrain Args：
            cpu_quota  example 0.25，means 25%
            mem_limit  example 1g
            memswap_limit  example 4g
            storage_opt example {"size":"2G"} 最小配置看docker
        '''
        resourceConstrainKey =  ["cpu_quota", "mem_limit","memswap_limit","storage_opt","device_read_bps","device_read_iops", "device_write_bps", "device_write_iops"]
        for key in resourceConstrain:
            if not key in resourceConstrainKey:
                return False, "resourceConstrainKey should in %s "%str(resourceConstrainKey)
        cpu_quota = self.get_from_dict(resourceConstrain, "cpu_quota")
        if cpu_quota:
            cpu_quota = int(cpu_quota*100000)
            resourceConstrain["cpu_quota"] = cpu_quota
        try:
            container:Container = self.client.containers.run(image=imageName, command=initCmd, name=containerName, ports =portMap, 
                detach=detach, tty=tty, **resourceConstrain)
            return True, container.id
        except Exception as err:
            return False, err
    

    def get_container(self,  containerName=None, containerID=None):
        container:Container = None
        try:
            if containerName:
                container = self.client.containers.get(containerName)
        except:
            pass
        try:
            if containerID:
                container = self.client.containers.get(containerID)
        except:
            pass
        return container
    def remove_container(self, containerName=None, containerID=None):
        container:Container =self.get_container(containerName, containerID)
        if not container:
            return True
        print(container.logs())
        try:
            container.remove(force=True)
        except:
            return False
        return True
    def stop_container(self, containerName=None, containerID=None, timeout=10):
        container:Container =self.get_container(containerName, containerID)
        if not container:
            return True
        try:
            container.stop(timeout=timeout)
        except Exception as err:
            print(err)
            return False
        return True
    def start_container(self, containerName=None, containerID=None):
        container:Container =self.get_container(containerName, containerID)
        if not container:
            return True
        try:
            container.start()
        except:
            return False
        return True
    def pause_container(self, containerName=None, containerID=None):
        container:Container =self.get_container(containerName, containerID)
        if not container:
            return True
        try:
            container.pause()
        except:
            return False
        return True
    def unpause_container(self, containerName=None, containerID=None):
        container:Container =self.get_container(containerName, containerID)
        if not container:
            return True
        try:
            container.unpause()
        except:
            return False
        return True
    def get_container_status(self, containerName=None, containerID=None):
        container:Container =self.get_container(containerName, containerID)
        if not container:
            return None
        return container.status
    def set_conatiner_network_constrain(self, containerName=None, containerID=None, uploadRate = str(1024*8), downloadRate = str(1024*8), cgroupClient:cgroup_util.CGroupClient=None):
        '''
            this method is used to set constrain of network usage for a running container.
            should be called everytime container restart
        '''
        print("set_conatiner_network_constrain",  uploadRate,downloadRate)
        container:Container = self.get_container(containerName, containerID)
        if not container:
            return False
        apiClient = docker.APIClient()   
        networkSettings = apiClient.inspect_container(container.id)["NetworkSettings"]
        sandboxKey = networkSettings["SandboxKey"]
        ok, interfaceName = cgroupClient.get_network_interface_name(sandboxKey)
        print("----------------------get_network_interface_name " ,interfaceName)
        if not ok:
            return False
        ok = cgroupClient.set_network_bps(interfaceName,uploadRate, downloadRate)
        print(ok)
        return ok

    def set_container_self_disk_constrain(self, containerName=None, containerID=None, resourceConstrain:dict={}, cgroupClient:cgroup_util.CGroupClient=None):
        '''
            this method is used to set constrain of disk usage for a running container.
            resourceConstrain is a dict:
            example:{
                "device_read_bps":"1024", // 1kB/s
                "device_read_iops:"10",
                "device_write_bps":"10240", //10kB/s
                "device_write_iops":"10"
            }
        '''
        container:Container = self.get_container(containerName, containerID)
        if not container:
            return False

        resourceConstrainKey =  ["device_read_bps","device_read_iops", "device_write_bps", "device_write_iops"]
        for key in resourceConstrain:
            if not key in resourceConstrainKey:
                return False, "resourceConstrainKey should in %s "%str(resourceConstrainKey)
        device_read_bps = self.get_from_dict(resourceConstrain,"device_read_bps")
        device_read_iops = self.get_from_dict(resourceConstrain, "device_read_iops")
        device_write_bps = self.get_from_dict(resourceConstrain, "device_write_bps")
        device_write_iops = self.get_from_dict(resourceConstrain, "device_write_iops")

        apiClient = docker.APIClient()   
        graphDriver = apiClient.inspect_container(container.id)["GraphDriver"]
        if graphDriver["Name"] == "devicemapper":
            deviceName = graphDriver["Data"]["DeviceName"]
            diskInfo = disk_util.DiskInfo()
            ok, deviceNumber = diskInfo.get_device_major_min(deviceName)
            if not ok:
                return False
            try:
                if device_read_bps:
                    ok = cgroupClient.set_blkio_read_bps_device(container.id, deviceNumber, device_read_bps,"w")
                    if not ok:
                        return False
                if device_write_bps:
                    ok = cgroupClient.set_blkio_write_bps_device(container.id, deviceNumber, device_write_bps,"w")
                    if not ok:
                        return False
                if device_read_iops:
                    ok = cgroupClient.set_blkio_read_iops_device(container.id, deviceNumber, device_read_iops,"w")
                    if not ok:
                        return False
                if device_write_iops:
                    ok = cgroupClient.set_blkio_write_iops_device(container.id, deviceNumber, device_write_iops,"w")
                    if not ok:
                        return False
            except:
                return False
        else:
            return False
        return True
    def exec(self, containerName=None, containerID=None, cmd=None):
        container:Container = self.get_container(containerName, containerID)
        if not container:
            return False
        ok = container.exec_run(cmd)    
        return ok