from .PM import *
import math

# Power consumption of Raspberry Pi 4 Model B
# @source Kaup, Fabian, Philip Gottschling, and David Hausheer.
# "PowerPi: Measuring and modeling the power consumption of the Raspberry Pi."
# In 39th Annual IEEE Conference on Local Computer Networks, pp. 236-243. IEEE, 2014.

class PMRaspberryPi4B(PM):
	def __init__(self):
		super().__init__()
		self.powerlist = [2.45, 2.78, 2.90, 3.03, 3.65, 3.66, 3.69, 3.71, 3.72, 4.14, 4.75]

	# cpu consumption in 100
	def power(self):
		cpu = self.host.getCPU()
		index = math.floor(cpu / 10)
		left = self.powerlist[index]
		right = self.powerlist[index + 1 if cpu%10 != 0 else index]
		alpha = (cpu / 10) - index
		return alpha * right + (1 - alpha) * left