from .IPSM import *

class IPSMBitbrain(IPSM):
	def __init__(self, ips_list, max_ips, duration, SLA):
		super().__init__()
		self.ips_list = ips_list
		self.max_ips = max_ips
		self.SLA = SLA
		self.duration = duration
		self.completedInstructions = 0
		self.totalInstructions = 0

	def getIPS(self):  # 获取当前时隙该容器任务所需的ips
		# if self.totalInstructions == 0:  # 在第一个时隙的时候for语句计算该容器任务在所有时隙所需的指令数总和
		# 	for ips in self.ips_list[:self.duration]: self.totalInstructions += ips * self.container.env.intervaltime
		# if self.completedInstructions < self.totalInstructions:
		ips = self.ips_list[self.container.env.interval % len(self.ips_list)]  # 返回当前时隙所需的ips, 对长度取余没用，七千后面都是0
		return ips

	def getMaxIPS(self):
		return self.max_ips