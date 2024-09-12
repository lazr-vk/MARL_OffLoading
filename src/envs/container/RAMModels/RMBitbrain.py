from .RM import *

class RMBitbrain(RM):
	def __init__(self, size_list, read_list, write_list):
		super().__init__()
		self.size_list = size_list
		self.read_list = read_list
		self.write_list = write_list

	def ram(self):
		# print('interval', self.container.env.interval)
		# print('startAt', self.container.startAt)
		size_list_count = self.container.env.interval % len(self.size_list)
		read_list_count = self.container.env.interval % len(self.read_list)
		write_list_count = self.container.env.interval % len(self.write_list)
		return self.size_list[size_list_count], self.read_list[read_list_count], self.write_list[write_list_count]