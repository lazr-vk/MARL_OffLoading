import torch as th
import numpy as np
from src.envs.RPiEdge import *
from src.envs.BitBrainWorkload import *
from src.envs.host.Host import *
from src.envs.container.Container import *
from smac.env import MultiAgentEnv

class OffloadingEnv(MultiAgentEnv):
    # def __init__(self, reward_sparse, obs_instead_of_state, total_power,
    #              router_bw, interval_time, hosts, new_containers, seed,
    #              num_step, state_last_action):
    def __init__(self, env_args, host, container):
        # 创建任务和主机
        self.totalpower = env_args["total_power"]
        self.totalbw = env_args["router_bw"]
        self.hostlimit = env_args["hosts"]
        self.containerlimit = env_args["new_containers"]
        self.duration = env_args["num_step"]
        self.hostlist = []
        self.hostinfo = []
        self.containerlist = []
        self.containerinfo = []
        self.intervaltime = env_args["interval_time"]  # 每个间隔的持续时间300s
        self.interval = 0
        self.inactiveContainers = []
        self.stats = None
        self.episode_limit = env_args["num_step"]
        self.current_step = 0
        self.pre_step = 0
        self.n_agents = len(container)
        self.n_actions = len(host)
        self.state = []
        # self.continuing_episode = continuing_episode
        # 初始化状态和观测
        # self.state = np.zeros((self.n_agents, 10))  # 假设每个agent的状态是一个10维向量
        # self.observations = np.zeros((self.n_agents, 10))  # 假设每个agent的观测是一个10维向量
        # self.action_space = [list(range(self.n_actions)) for _ in range(self.n_agents)]
        self.obs_instead_of_state = env_args["obs_instead_of_state"]
        self.reward_sparse = env_args["reward_sparse"]
        self.state_last_action = env_args["state_last_action"]
        self.seed = env_args["seed"]
        self.addHostlistInit(host)
        self.addContainerListInit(container)
        # 创建主机状态的时间序列
        self.host_time_series = np.zeros((1, 3 * len(self.hostlist)))
        self.container_time_series = np.zeros((1, 3 * len(self.containerlist)))
        self.exe_time = np.full(len(self.containerlist), -1.0)
        self.trans_time = np.full(len(self.containerlist), -1.0)
        self.local_exe_time = np.full(len(self.containerlist), -1.0)
        self.all_local_time = np.full(len(self.containerlist), -1.0)

    def addHostInit(self, IPS, RAM, Disk, Bw, Latency, Powermodel, Position):
        assert len(self.hostlist) < self.hostlimit
        host = Host(len(self.hostlist)+2, IPS, RAM, Disk, Bw, Latency, Powermodel, Position, self)
        self.hostlist.append(host)

    def addHostlistInit(self, hostList):
        assert len(hostList) == self.hostlimit
        for IPS, RAM, Disk, Bw, Latency, Powermodel, Position in hostList:
            self.addHostInit(IPS, RAM, Disk, Bw, Latency, Powermodel, Position)

    def addContainerInit(self, CreationID, CreationInterval, IPSModel, RAMModel, DiskModel, Position, HostModel):
        container = Container(len(self.containerlist), CreationID, CreationInterval, IPSModel, RAMModel, DiskModel,
                              Position, HostModel, self, HostID=-1)
        self.containerlist.append(container)
        # return container

    def addContainerListInit(self, containerInfoList):
        # deployed = containerInfoList[:min(len(containerInfoList), self.containerlimit - self.getNumActiveContainers())]
        # deployedContainers = []
        for CreationID, CreationInterval, IPSModel, RAMModel, DiskModel, Position, HostModel in containerInfoList:
            self.addContainerInit(CreationID, CreationInterval, IPSModel, RAMModel, DiskModel, Position, HostModel)
        # self.containerlist += [None] * (self.containerlimit - len(self.containerlist))
        # return [container.id for container in deployedContainers]

    def getContainersOfHost(self, hostID):  # 获取部署在hostID上的容器ID
        containers = []
        for container in self.containerlist:
            if container and container.hostid == hostID - 2:  # 检查是否有容器部署在hostID的主机上
                containers.append(container.id)  # container.id表示容器ID
        return containers

    def getHostByID(self, hostID):  # 通过id查询主机信息
        return self.hostlist[hostID]

    def getContainerByID(self, containerID):
        return self.containerlist[containerID]

    def getNumberofContainers(self, hostID, decision):
        containerIDs = []
        for cid, hid in enumerate(decision):
            if hid.item() == hostID:
                containerIDs.append(cid)
        return containerIDs

    def getPlacementPossible(self, containerID, hostID):
        container = self.containerlist[containerID]
        ipsreq = container.getBaseIPS()
        ramsizereq, ramreadreq, ramwritereq = container.getRAM()
        disksizereq, diskreadreq, diskwritereq = container.getDisk()
        if hostID == len(self.hostlist):
            host = container.hostmodel
            ipsavailable = host.ipsCap
            ramsizeav = host.ramCap.size
            disksizeav = host.diskCap.size
        else:
            host = self.hostlist[hostID]
            ipsavailable = host.getIPSAvailable()
            ramsizeav, ramreadav, ramwriteav = host.getRAMAvailable()
            disksizeav, diskreadav, diskwriteav = host.getDiskAvailable()
        return (ipsreq <= ipsavailable and \
                ramsizereq <= ramsizeav and \
                # ramreadreq <= ramreadav and \
                # ramwritereq <= ramwriteav and \
                disksizereq <= disksizeav \
                # diskreadreq <= diskreadav and \
                # diskwritereq <= diskwriteav
                )

    def allocateByDecision(self, actions):
        transmission = []
        migrations = []
        # routerBwToEach = self.totalbw / len(actions)
        routerBwToEach = 10000
        for cid, hid in enumerate(actions):
            container = self.getContainerByID(cid)
            assert container.getHostID() == -1
            if hid.item() == len(self.hostlist):  # 本地执行，传输时间为0
                # if self.getPlacementPossible(cid, hid.item()):  # 判断该容器任务是否能部署在该主机上（通过判断任务需要的资源主机是不是能够满足）
                migrations.append((cid, hid.item()))
                lastMigrationTime = 0
                container.hostid = hid.item()
                container.hostmodel.priority_list.append(cid)
                # destroy pointer to this unallocated container as book-keeping is done by workload model
                # else:
                #     migrations.append((cid, hid.item()))
                #     container.hostid = hid.item()
                #     lastMigrationTime = 0
            else:  # 边缘执行
                host = self.getHostByID(hid)
                numberAllocToHost = len(self.getNumberofContainers(hid.item(), actions))  # getMigrationToHost获取迁移到hid主机上的任务列表
                # allocbw = min(self.getHostByID(hid).bwCap.downlink / numberAllocToHost, routerBwToEach)
                # if self.getPlacementPossible(cid, hid.item()):  # 判断该容器任务是否能部署在该主机上（通过判断任务需要的资源主机是不是能够满足）
                migrations.append((cid, hid.item()))
                lastMigrationTime = container.allocate(hid.item(), routerBwToEach)
                host.priority_list.append(cid)
                # destroy pointer to this unallocated container as book-keeping is done by workload model
                # else:
                #     migrations.append((cid, hid.item()))
                #     container.hostid = -1
                #     lastMigrationTime = 0
            self.trans_time[cid] = lastMigrationTime
        return migrations

    def execute(self, action):
        for h in self.hostlist:  # 边缘执行
            h.currentips = h.ipsCap
            h.execute()
            h.priority_list = []
            # exe_info.append(host_exe_info)
        for c in self.containerlist:  # 本地执行
            c.execute()
            c.priority_list = []
            # exe_info.append(host_exe_info)

    def transmission(self):
        for c in self.containerlist:
            c.hostid = -1
        self.trans_time[:] = -1
        self.exe_time[:] = -1
        self.local_exe_time[:] = -1
        self.all_local_time[:] = -1

    def all_local_exe(self):
        for c in self.containerlist:  # 本地执行
            c.execute(all_local=True)


    def step(self, actions):
        """执行动作，并返回奖励、是否终止、信息"""
        # print('step_interval', self.interval)
        # 时间设为1s，1s内获得奖励，1s到2s奖励为0，2s以上获得惩罚
        # 将任务的hostid修改为卸载决策的主机，并计算传输时间
        self.transmission()
        migrations = self.allocateByDecision(actions)
        # for c in self.containerlist:
        #     print("任务：", c.id)
        #     print("目标主机:", c.hostid)
        # 将任务按优先级排序，并执行任务，计算时间和能耗
        self.execute(actions)
        self.all_local_exe()
        # for c in self.containerlist:
        #     print("任务：", c.id)
        #     print("目标主机:", c.hostid)
        a = (self.all_local_time - (self.trans_time + self.local_exe_time + self.exe_time)) / self.all_local_time
        reward = np.sum((self.all_local_time - (self.trans_time + self.local_exe_time + self.exe_time)) / self.all_local_time)
        self.interval += 1
        self.current_step += 1
        # print('self.current_step', self.current_step)
        # print(self.episode_limit)
        # print(self.current_step)
        terminated = (self.current_step - self.pre_step) >= self.episode_limit
        info = {"step": self.current_step}

        # # 更新状态和观测
        # self.state += np.random.random((self.n_agents, 10))  # 随机更新状态
        # self.observations += np.random.random((self.n_agents, 10))  # 随机更新观测

        return reward, terminated, info

    def get_obs_agent(self, agent_id):
        """返回指定agent的观测"""
        return self.observations[agent_id]

    def get_obs_size(self):
        """返回观测的维度"""
        return self.observations.shape[1]

    def get_localhost_state(self, container):
        localhost_info = dict()
        localhost_info['cpu'] = [container.get_local_cpu_usage()]
        localhost_info['ram'] = [container.get_local_ram_usage()]
        localhost_info['disk'] = [container.get_local_disk_usage()]
        cpulist, ramlist, disklist = localhost_info['cpu'], localhost_info['ram'], localhost_info['disk']
        datapoint = np.concatenate([cpulist, ramlist, disklist]).reshape(1, -1)
        return datapoint

    def get_host_state(self, host):
        hostinfo = dict()
        # print(self.interval)
        hostinfo['interval'] = self.interval
        hostinfo['cpu'] = [host.getCPU() / 100]  # cpu使用率
        hostinfo['numcontainers'] = [len(self.getContainersOfHost(host.id))]  # 运行的容器任务数量
        hostinfo['power'] = [host.getPower()]  # 每个主机的功耗(根据cpu利用率选择能耗)
        hostinfo['baseips'] = [host.getBaseIPS()]  # 运行在主机上的所有容器任务ips和
        hostinfo['ipsavailable'] = [host.getIPSAvailable()]  # 每个主机可用的ips(最大ips-baseips)
        hostinfo['ipscap'] = [host.ipsCap]  # 每个主机的最大ips
        # hostinfo['apparentips'] = [host.getApparentIPS()]
        hostinfo['ram'] = [host.getCurrentRAM()]  # 获取部署在该主机上所有任务对内存需求的和
        hostinfo['ramavailable'] = [host.getRAMAvailable()]  # 获取当前时刻该主机可用的内存
        hostinfo['disk'] = [host.getCurrentDisk()]
        hostinfo['diskavailable'] = [host.getDiskAvailable()]
        cpulist, ramlist, disklist = hostinfo['cpu'], [i[0] / host.ramCap.size for i in hostinfo['ram']], [i[0] / host.diskCap.size for i in hostinfo['disk']]
        datapoint = np.concatenate([cpulist, ramlist, disklist]).reshape(1, -1)
        return datapoint

    def get_containers_state(self, container):
        containerinfo = dict()
        containerinfo['interval'] = self.interval
        containerinfo['ips'] = [container.getBaseIPS() if container else 0]  # 返回当前时刻任务所需的ips
        # containerinfo['apparentips'] = [container.getApparentIPS() if container else 0]  # 返回所部署的主机可用的ips
        containerinfo['ram'] = [container.getRAM() if container else 0]
        containerinfo['disk'] = [container.getDisk() if container else 0]
        containerinfo['creationids'] = [container.creationID if container else -1]
        containerinfo['hostalloc'] = [container.getHostID() if container else -1]
        ipslist, ramlist, disklist = containerinfo['ips'], [i[0] for i in containerinfo['ram']], [i[0] for i in containerinfo['disk']]
        datapoint = np.concatenate([ipslist, ramlist, disklist]).reshape(1, -1)
        return datapoint

    def get_state(self):
        """返回全局状态"""
        host_state = np.concatenate([self.get_host_state(c) for c in self.hostlist], axis=1)
        # print(host_state)
        container_state = np.concatenate([self.get_containers_state(c) for c in self.containerlist], axis=1)
        local_host_state = np.concatenate([self.get_localhost_state(c) for c in self.containerlist], axis=1)
        if self.interval != 0:
            self.host_time_series = np.append(self.host_time_series, host_state, axis=0)
            self.hostinfo.append(host_state)
            self.container_time_series = np.append(self.container_time_series, container_state, axis=0)
            self.containerinfo.append(container_state)
        state = np.concatenate((container_state, local_host_state, host_state), axis=1).reshape(-1)
        # self.saveAllContainerInfo()
        # self.saveMetrics(destroyed, migrations)
        # self.saveSchedulerInfo(selectedcontainers, decision, schedulingtime)
        return state

    def get_state_size(self):
        """返回状态的维度"""
        """Returns the size of the global state."""
        # if self.obs_instead_of_state:
        #     return self.get_obs_size() * self.n_agents
        return self.get_state().size

    def get_obs(self):
        """返回所有agent的观测列表，按任务特征，es特征，本地主机特征拼接"""
        obs = []
        for c in self.containerlist:
            container_obs = self.get_containers_state(c)
            avail_action = c.getCommunicationRange()
            for cindex, cid in enumerate(avail_action):

                if cid==0:
                    cid_obs = np.full((1, 3), -1)
                else:
                    if cindex == len(self.hostlist):
                        cid_obs = self.get_localhost_state(c)
                    else:
                        cid_obs = self.get_host_state(self.getHostByID(cindex))
                container_obs = np.append(container_obs, cid_obs, axis=1)
            obs.append(container_obs.reshape(-1))
        return obs

    def get_avail_actions(self):
        """返回所有agent的可用动作列表"""
        # avail_actions = []
        return [c.getCommunicationRange() for c in self.containerlist]

    def get_avail_agent_actions(self, agent_id):
        """返回指定agent的可用动作"""
        return self.action_space[agent_id]

    def get_total_actions(self):
        """返回agent可以采取的总动作数量"""
        return self.n_actions

    def reset(self):
        """重置环境，返回初始的观测和状态"""
        self.current_step = 0
        # self.state = np.zeros((self.n_agents, 10))
        # self.observations = np.zeros((self.n_agents, 10))
        return self.get_obs(), self.get_state()

    def render(self):
        """渲染环境（可选）"""
        print(f"Step: {self.current_step}, State: {self.state}")

    def close(self):
        """关闭环境"""
        print("Closing environment")

    def seed(self, seed=None):
        """设置随机种子"""
        np.random.seed(seed)

    def save_replay(self):
        """保存回放（可选）"""
        print("Saving replay")

    def get_env_info(self):
        """返回环境的元信息"""
        env_info = {
            # "state_shape": self.get_state_size(),57
            # "obs_shape": self.get_obs_size(),
            # "n_actions": self.get_total_actions(),
            # "n_agents": self.n_agents,
            # "episode_limit": self.episode_limit
            "state_shape": 3 * self.n_actions + 3 * self.n_agents + 3 * self.n_agents,
            "obs_shape": 3 + 3 * (self.n_actions + 1),
            "n_actions": self.n_actions + 1,
            "n_agents": self.n_agents,
            "episode_limit": self.episode_limit
        }
        return env_info