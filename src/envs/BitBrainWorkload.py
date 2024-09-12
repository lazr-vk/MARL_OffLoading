import random

from .Workload import *
from .container.IPSModels.IPSMBitbrain import *
from .container.RAMModels.RMBitbrain import *
from .container.DiskModels.DMBitbrain import *
from .position.COORD import *
from src.envs.host.Local_Host import *
from random import gauss, randint
from os import path, makedirs, listdir, remove
import wget
from zipfile import ZipFile
import shutil
import pandas as pd
import warnings
warnings.simplefilter("ignore")

# Intel Pentium III gives 2054 MIPS at 600 MHz
# Source: https://archive.vn/20130205075133/http://www.tomshardware.com/charts/cpu-charts-2004/Sandra-CPU-Dhrystone,449.html
ips_multiplier = 2054.0 / (2 * 600)  # 每个时钟周期可以执行的指令数

class BWGD2(Workload):
	def __init__(self):
		super().__init__()
		dataset_path = 'datasets/bitbrain/'
		if not path.exists(dataset_path):
			makedirs(dataset_path)
			print('Downloading Bitbrain Dataset')
			url = 'http://gwa.ewi.tudelft.nl/fileadmin/pds/trace-archives/grid-workloads-archive/datasets/gwa-t-12/rnd.zip'
			filename = wget.download(url); zf = ZipFile(filename, 'r'); zf.extractall(dataset_path); zf.close()
			for f in listdir(dataset_path+'rnd/2013-9/'): shutil.move(dataset_path+'rnd/2013-9/'+f, dataset_path+'rnd/')
			shutil.rmtree(dataset_path+'rnd/2013-7'); shutil.rmtree(dataset_path+'rnd/2013-8')
			shutil.rmtree(dataset_path+'rnd/2013-9'); remove(filename)
		self.dataset_path = dataset_path
		self.disk_sizes = [1, 2, 3]
		self.meanSLA, self.sigmaSLA = 20, 3
		self.possible_indices = [9, 21, 28, 29, 31, 34, 106, 211, 219, 226, 228, 236, 256, 261, 267, 268, 269, 272, 274,
								 276, 280, 286, 311, 324, 332, 333, 375, 380, 383, 384, 385, 392, 407, 408, 411, 413,
								 420, 440, 488, 493, 494, 495]
		# for i in range(1, 500):
		# 	df = pd.read_csv(self.dataset_path+'rnd/'+str(i)+'.csv', sep=';\t')
		# 	# a = (ips_multiplier*df['CPU usage [MHZ]']).to_list()
		# 	# b = a[10]
		# 	if (ips_multiplier*df['CPU usage [MHZ]']).to_list()[10] < 3000 and (ips_multiplier*df['CPU usage [MHZ]']).to_list()[10] > 500:
		# 		self.possible_indices.append(i)

	def generateNewContainers(self, num_containers, seed, num_step, hosts):
		workloadlist = []
		random.seed(seed)
		interval = 0
		print(self.possible_indices)
		position_df = pd.read_csv('datasets/container_tasks.csv')
		for i in range(num_containers):
			CreationID = self.creation_id
			index = self.possible_indices[randint(0, len(self.possible_indices)-1)]
			df = pd.read_csv('./datasets/Container_services/test/' + str(i) + '.csv', sep=';')
			sla = gauss(self.meanSLA, self.sigmaSLA)
			host = hosts[i]
			IPSModel = IPSMBitbrain((ips_multiplier*df['CPU usage [MHZ]']).to_list(),
									(ips_multiplier*df['CPU capacity provisioned [MHZ]']).to_list()[0],
									num_step, sla)
			RAMModel = RMBitbrain((df['Memory usage [KB]']).to_list(), (df['Network received throughput [KB/s]']).to_list(), (df['Network transmitted throughput [KB/s]']).to_list())
			disk_size  = self.disk_sizes[index % len(self.disk_sizes)]
			DiskModel = DMBitbrain(disk_size, (df['Disk read throughput [KB/s]']).to_list(), (df['Disk write throughput [KB/s]']).to_list())
			Position = PositionModel(position_df['x'][i], position_df['y'][i])
			workloadlist.append((CreationID, interval, IPSModel, RAMModel, DiskModel, Position, host))
			self.creation_id += 1
		self.createdContainers += workloadlist
		self.deployedContainers += [False] * len(workloadlist)
		return self.getUndeployedContainers()