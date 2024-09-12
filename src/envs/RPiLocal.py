import numpy as np
import pandas as pd
from src.envs.host.Disk import *
from src.envs.host.RAM import *
from src.envs.host.Bandwidth import *
from .position.COORD import *
from src.metrics.powermodels.PMRaspberryPi4B import *
from src.metrics.powermodels.PMRaspberryPi4B8G import *
from .host.Local_Host import LocalHost

class RPiLocal():
	def __init__(self, num_hosts):
		self.num_hosts = num_hosts
		self.edge_hosts = round(num_hosts * 2)
		self.types = {
			'UE4B':
				{
					'IPS': 1024,
					'RAMSize': 4295,
					'RAMRead': 372.0,
					'RAMWrite': 200.0,
					'DiskSize': 32212,
					'DiskRead': 13.42,
					'DiskWrite': 1.011,
					'BwUp': 5000,
					'BwDown': 5000,
					'Power': 'PMRaspberryPi4B'
				},
            'UE4B8G':
                {
                    'IPS': 2400,
                    'RAMSize': 4295,
                    'RAMRead': 372.0,
                    'RAMWrite': 200.0,
                    'DiskSize': 32212,
                    'DiskRead': 13.42,
                    'DiskWrite': 1.011,
                    'BwUp': 5000,
                    'BwDown': 5000,
                    'Power': 'PMRaspberryPi4B'
                },
 		}

	def generateHosts(self):
		hosts = []
		types = ['UE4B'] * int(self.num_hosts/2) + ['UE4B8G'] * int(self.num_hosts/2)
		position_df = pd.read_csv('datasets/host_positions.csv')
		for i in range(self.num_hosts):
			typeID = types[i]
			IPS = self.types[typeID]['IPS']
			Ram = RAM(self.types[typeID]['RAMSize'], self.types[typeID]['RAMRead']*5, self.types[typeID]['RAMWrite']*5)
			Disk_ = Disk(self.types[typeID]['DiskSize'], self.types[typeID]['DiskRead']*5, self.types[typeID]['DiskWrite']*10)
			Bw = Bandwidth(self.types[typeID]['BwUp'], self.types[typeID]['BwDown'])
			Power = eval(self.types[typeID]['Power']+'()')
			Latency = 0.003 if i < self.edge_hosts else 0.076
			Position = PositionModel(position_df['x'][i], position_df['y'][i])
			host = LocalHost(IPS, Ram, Disk_, Bw, Latency, Power, Position)
			hosts.append(host)
		return hosts