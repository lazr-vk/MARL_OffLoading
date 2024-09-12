from .Disk import *
from .RAM import *
from .Bandwidth import *

class LocalHost():
    # IPS = Million Instructions per second capacity
    # RAM = Ram in MB capacity
    # Disk = Disk characteristics capacity
    # Bw = Bandwidth characteristics capacity
    def __init__(self, IPS, RAM, Disk, Bw, Latency, Powermodel, Position):
        self.ipsCap = IPS
        self.ramCap = RAM
        self.diskCap = Disk
        self.bwCap = Bw
        self.latency = Latency
        self.powermodel = Powermodel
        self.position = Position
        self.powermodel.allocHost(self)
        self.powermodel.host = self
        self.priority_list = []
        self.partiallyexe_list = []

    def getPower(self):
        return self.powermodel.power()

    def getPowerFromIPS(self, ips):
        return self.powermodel.powerFromCPU(min(100, 100 * (ips / self.ipsCap)))

    def getCPU(self):  # 返回主机的cpu使用率 如果上一时刻是在本地执行的则返回
        ips = self.getApparentIPS()
        return 100 * (ips / self.ipsCap)  # ips表示部署在该主机上的容器任务所需的ips

    def getBaseIPS(self):  # 获取该主机当前执行的容器任务所需的ips
        # Get base ips count as sum of min ips of all containers
        ips = 0
        containers = self.env.getContainersOfHost(self.id)  # 获取当前主机上执行的containerid
        for containerID in containers:
            ips += self.env.getContainerByID(containerID).getBaseIPS()
        # assert ips <= self.ipsCap
        return ips

    def getApparentIPS(self):  # 计算在该主机上执行的容器任务的ips和
        # Give containers remaining IPS for faster execution
        ips = 0 # 检查是否有容器任务在主机上执行
        for containerID in self.priority_list:
            ips += self.env.getContainerByID(containerID).getApparentIPS()  # 计算在该主机上执行的容器任务的ips和
        # assert int(ips) <= self.ipsCap
        return int(ips)

    def getIPSAvailable(self):  # 返回当前时刻可用的ips有多少
        # IPS available is ipsCap - baseIPS
        # When containers allocated, existing ips can be allocated to
        # the containers
        return self.ipsCap - self.getBaseIPS()

    def getCurrentRAM(self):
        size, read, write = 0, 0, 0
        containers = self.env.getContainersOfHost(self.id)
        for containerID in containers:
            s, r, w = self.env.getContainerByID(containerID).getRAM()
            size += s;
            read += r;
            write += w
        # assert size <= self.ramCap.size
        # assert read <= self.ramCap.read
        # assert write <= self.ramCap.write
        return size, read, write

    def getRAMAvailable(self):
        size, read, write = self.getCurrentRAM()
        return self.ramCap.size - size, self.ramCap.read - read, self.ramCap.write - write

    def getCurrentDisk(self):
        size, read, write = 0, 0, 0
        containers = self.env.getContainersOfHost(self.id)
        for containerID in containers:
            s, r, w = self.env.getContainerByID(containerID).getDisk()
            size += s;
            read += r;
            write += w
        assert size <= self.diskCap.size
        assert read <= self.diskCap.read
        assert write <= self.diskCap.write
        return size, read, write

    def getDiskAvailable(self):
        size, read, write = self.getCurrentDisk()
        return self.diskCap.size - size, self.diskCap.read - read, self.diskCap.write - write

    def execute(self):
        # 按优先级排序任务
        # 执行
        exe_info = []
        exeTime = 0
        exeTime = 0
        if self.partiallyexe_list:
            for c in self.partiallyexe_list[:]:
                container = self.env.getContainerByID(c)
                print(self.env.interval)
                containerIPS = container.remainedips[self.env.interval - 1]
                execTime = containerIPS / self.ipsCap
                self.currentips -= containerIPS
                exeTime += execTime
                self.partiallyexe_list.remove(c)
        for c in self.priority_list:
            container = self.env.getContainerByID(c)
            currentIPS = container.getBaseIPS()
            execTime = currentIPS / self.ipsCap
            exeTime += execTime
            self.env.exe_time[container.id] = execTime
            # print(execTime)
            exe_info.append(c_exeinfo)
        return exe_info


