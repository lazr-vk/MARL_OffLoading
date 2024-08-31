import numpy as np


class Container():
	# IPS = ips requirement
	# RAM = ram requirement in MB
	# Size = container size in MB
	def __init__(self, ID, creationID, creationInterval, IPSModel, RAMModel, DiskModel, Position, Environment, HostID = -1):
		self.id = ID
		self.creationID = creationID
		self.ipsmodel = IPSModel
		self.ipsmodel.allocContainer(self)
		self.sla = self.ipsmodel.SLA
		self.rammodel = RAMModel
		self.rammodel.allocContainer(self)
		self.diskmodel = DiskModel
		self.diskmodel.allocContainer(self)
		self.hostid = HostID
		self.env = Environment
		self.position = Position
		self.createAt = creationInterval
		self.startAt = self.env.interval
		self.totalExecTime = 0
		self.totalMigrationTime = 0
		self.comm_radius = 2
		self.active = True
		self.destroyAt = -1
		self.lastContainerSize = 0
		# self.coord = COORDModel
	def getBaseIPS(self):
		return self.ipsmodel.getIPS()  # 获取该任务当前时刻所需的ips

	def getApparentIPS(self):
		hostBaseIPS = self.getHost().getBaseIPS()  # getHost()获取容器任务当前是在哪个主机, getBaseIPS()获取该主机当前执行的容器任务所需的ips
		hostIPSCap = self.getHost().ipsCap  # ipsCap表示主机的ips
		canUseIPS = (hostIPSCap - hostBaseIPS) / len(self.env.getContainersOfHost(self.hostid))
		return min(self.ipsmodel.getMaxIPS(), self.getBaseIPS() + canUseIPS)  # 返回min(该容器任务在所有时隙中所需最大的ips，当前时间步该容器任务所需的ips + 可以用的ips)

	def getRAM(self):  # 返回当前时刻对内存大小，读写速率的要求
		rsize, rread, rwrite = self.rammodel.ram()
		self.lastContainerSize = rsize
		return rsize, rread, rwrite

	def getDisk(self):
		return self.diskmodel.disk()

	def getContainerSize(self):  # 返回当前时刻容器任务的大小
		if self.lastContainerSize == 0: self.getRAM()
		return self.lastContainerSize  # 当前时刻容器任务的大小

	def getHostID(self):
		return self.hostid

	def getHost(self):  # 通过hostid获得主机的信息
		return self.env.getHostByID(self.hostid)

	def getCommunicationRange(self):
		comm_host = []
		for c in self.env.hostlist:
			distance = self.calculate_distance(c.position)
			if distance < self.comm_radius:
				comm_host.append(1)
			else:
				comm_host.append(0)
		return comm_host

	def calculate_distance(self, Position):
		return self.position.calculate_distance(Position)

	def allocate(self, hostID, allocBw):  # 将容器任务的hostid变为目标服务器，并计算整个部署所耗的时间
		# Migrate if allocated to a different host
		# Migration time is sum of network latency
		# and time to transfer container based on
		# network bandwidth and container size.
		lastMigrationTime = 0
		if self.hostid != hostID:
			lastMigrationTime += self.getContainerSize() / allocBw
			lastMigrationTime += abs(self.env.hostlist[self.hostid].latency - self.env.hostlist[hostID].latency)  # abs获得绝对值
		self.hostid = hostID
		return lastMigrationTime

	def execute(self, lastMigrationTime):  # 每个时隙300s，减去迁移时间后就是可执行时间，可执行时间乘ips就是该时刻完成的指令数
		# Migration time is the time to migrate to new host
		# Thus, execution of task takes place for interval
		# time - migration time with apparent ips
		assert self.hostid != -1
		self.totalMigrationTime += lastMigrationTime
		execTime = self.env.intervaltime - lastMigrationTime
		apparentIPS = self.getApparentIPS()
		requiredExecTime = (self.ipsmodel.totalInstructions - self.ipsmodel.completedInstructions) / apparentIPS if apparentIPS else 0
		self.totalExecTime += min(execTime, requiredExecTime)
		self.ipsmodel.completedInstructions += apparentIPS * min(execTime, requiredExecTime)

	def allocateAndExecute(self, hostID, allocBw):
		self.execute(self.allocate(hostID, allocBw))

	def destroy(self):
		self.destroyAt = self.env.interval
		self.hostid = -1
		self.active = False


