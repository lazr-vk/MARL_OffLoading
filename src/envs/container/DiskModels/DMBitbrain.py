from .DM import *

class DMBitbrain(DM):
	def __init__(self, constant_size, read_list, write_list):
		super().__init__()
		self.constant_size = constant_size
		self.read_list = read_list
		self.write_list = write_list

	def disk(self):  # 返回当前时刻磁盘读写速率的指标
		read_list_count = self.container.env.interval % len(self.read_list)
		write_list_count = self.container.env.interval % len(self.write_list)
		return self.constant_size, self.read_list[read_list_count], self.write_list[write_list_count]