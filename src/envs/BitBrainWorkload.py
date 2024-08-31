import random

from .Workload import *
from .container.IPSModels.IPSMBitbrain import *
from .container.RAMModels.RMBitbrain import *
from .container.DiskModels.DMBitbrain import *
from .position.COORD import *
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
		self.possible_indices = []
		for i in range(1, 500):
			df = pd.read_csv(self.dataset_path+'rnd/'+str(i)+'.csv', sep=';\t')
			# a = (ips_multiplier*df['CPU usage [MHZ]']).to_list()
			# b = a[10]
			if (ips_multiplier*df['CPU usage [MHZ]']).to_list()[10] < 3000 and (ips_multiplier*df['CPU usage [MHZ]']).to_list()[10] > 500:
				self.possible_indices.append(i)

	def generateNewContainers(self, num_containers, seed, num_step):
		workloadlist = []
		random.seed(seed)
		interval = 0
		position_df = pd.read_csv('datasets/container_tasks.csv')
		for i in range(num_containers):
			CreationID = self.creation_id
			index = self.possible_indices[randint(0, len(self.possible_indices)-1)]
			df = pd.read_csv(self.dataset_path+'rnd/'+str(index)+'.csv', sep=';\t')
			sla = gauss(self.meanSLA, self.sigmaSLA)
			IPSModel = IPSMBitbrain((ips_multiplier*df['CPU usage [MHZ]']).to_list(),
									(ips_multiplier*df['CPU capacity provisioned [MHZ]']).to_list()[0],
									num_step, sla)
			RAMModel = RMBitbrain((df['Memory usage [KB]']/4000).to_list(), (df['Network received throughput [KB/s]']/1000).to_list(), (df['Network transmitted throughput [KB/s]']/1000).to_list())
			disk_size  = self.disk_sizes[index % len(self.disk_sizes)]
			DiskModel = DMBitbrain(disk_size, (df['Disk read throughput [KB/s]']/4000).to_list(), (df['Disk write throughput [KB/s]']/12000).to_list())
			Position = PositionModel(position_df['x'][i], position_df['y'][i])
			workloadlist.append((CreationID, interval, IPSModel, RAMModel, DiskModel, Position))
			self.creation_id += 1
		self.createdContainers += workloadlist
		self.deployedContainers += [False] * len(workloadlist)
		return self.getUndeployedContainers()