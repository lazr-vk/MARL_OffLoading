import json
import random
from collections import Counter
from scipy import stats
import pandas as pd
import argparse
import time
import numpy as np
import scipy

def load_json(addr):
    with open(addr, 'r') as load_f:
        load_data = json.load(load_f)
        return load_data

if __name__ == '__main__':
    # total_step = 1440002
    total_step = 576
    possible_indices = []
    ips_multiplier = 2054.0 / (2 * 600)
    # for i in range(1, 500):
    #     df = pd.read_csv('./datasets/bitbrain/rnd/' + str(i) + '.csv', sep=';\t', engine='python')
    #     # a = (ips_multiplier*df['CPU usage [MHZ]']).to_list()
    #     # b = a[10]
    #     if (ips_multiplier * df['CPU usage [MHZ]']).to_list()[10] < 3000 and \
    #             (ips_multiplier * df['CPU usage [MHZ]']).to_list()[10] > 500:
    #         possible_indices.append(i)

    print('Generating containerized service ...')
    variance_addr = './datasets/quantified_date/docker_variance.json'
    average_addr = './datasets/quantified_date/docker_average.json'
    target_docker_list = list(range(1, 19))
    var_dict = load_json(variance_addr)
    avg_dict = load_json(average_addr)
    # resource_kind = ['mem', 'cpu', 'disk', 'bandwidth']
    resource_kind = ['mem', 'cpu', 'disk']
    # out_data = [[], [], [], [], [], []]  # time, kind, memory, cpu, disk, bandwidth
    # for target_docker in target_docker_list:  # 若是每个类型任务添加多个任务就改for循环
    cpuCap = 1024  # MHZ
    ramCap = 2024
    diskCap = np.random.uniform(100, 150)
    diskreadCap = np.random.uniform(10, 15)
    diskwriteCap = np.random.uniform(1, 5)
    ramreadCap = np.random.uniform(40, 45)
    ramwriteCap = np.random.uniform(30, 35)
    number_task = 19
    # c = 5
    for c in range(number_task):
        # index = possible_indices[c]
        a = len(var_dict)
        f = len(possible_indices)
        target_docker = ((c % len(var_dict)) + 1)
        # df = pd.read_csv('./datasets/bitbrain/rnd/' + str(index) + '.csv', sep=';\t', engine='python')

        cur_var_dict = var_dict[str(target_docker)]
        cur_avg_dict = avg_dict[str(target_docker)]
        out_data = [[], [], [], [], [], [], [], [], [], [], []]
        # for one_log in range(len(cur_var_dict['mem'])):
        for one_log in range(total_step):
            cur_time = one_log * 300
            out_data[0].append(cur_time)
            out_data[1].append(target_docker)
            step_per_day = one_log % 288
            # print(step_per_day)
            # if step_per_day == 287:
            #     print('1')
            for one_resource in resource_kind:
                one_var = cur_var_dict[one_resource][step_per_day]
                one_avg = cur_avg_dict[one_resource][step_per_day]
                np.random.seed(int(time.time()))
                s = np.random.normal(one_avg, np.sqrt(one_var), 1)[0]
                while s < 0 or s > 100:
                    s = np.random.normal(one_avg, np.sqrt(one_var), 1)[0]

                if one_resource == 'cpu':
                    cpu_usage = cpuCap * (s / 100) + 500
                    out_data[2].append(cpuCap)
                    out_data[3].append(cpu_usage)
                elif one_resource == 'mem':
                    ram_usage = ramCap * (s / 100) + 500
                    ram_read_throught = ramreadCap * (s / 100)
                    ram_write_throught = ramwriteCap * (s / 100)
                    out_data[4].append(ramCap)
                    out_data[5].append(ram_usage)
                    out_data[6].append(ram_read_throught)
                    out_data[7].append(ram_write_throught)
                elif one_resource == 'disk':
                    disk_size = diskCap * (s / 100)
                    disk_read_throught = diskreadCap * (s / 100)
                    disk_write_throught = diskwriteCap * (s / 100)
                    out_data[8].append(disk_size)
                    out_data[9].append(disk_read_throught)
                    out_data[10].append(disk_write_throught)

        all_docker_df = pd.DataFrame(
            {
                'Timestamp [ms]': [float(one) for one in out_data[0]],
                'Service kind': [float(one) for one in out_data[1]],
                'CPU capacity provisioned [MHZ]': [float(one) for one in out_data[2]],
                'CPU usage [MHZ]': [float(one) for one in out_data[3]],
                'Memory capacity provisioned [KB]': [float(one) for one in out_data[4]],
                'Memory usage [KB]': [float(one) for one in out_data[5]],
                'Network received throughput [KB/s]': [float(one) for one in out_data[6]],
                'Network transmitted throughput [KB/s]': [float(one) for one in out_data[7]],
                'Disk capacity provisioned': [float(one) for one in out_data[8]],
                'Disk read throughput [KB/s]': [float(one) for one in out_data[9]],
                'Disk write throughput [KB/s]': [float(one) for one in out_data[10]]
            })
        columns_to_round = [
            'CPU capacity provisioned [MHZ]',
            'CPU usage [MHZ]',
            'Memory capacity provisioned [KB]',
            'Memory usage [KB]',
            'Network received throughput [KB/s]',
            'Network transmitted throughput [KB/s]',
            'Disk capacity provisioned',
            'Disk read throughput [KB/s]',
            'Disk write throughput [KB/s]'
        ]

        all_docker_df[columns_to_round] = all_docker_df[columns_to_round].round(4)
        all_docker_df.to_csv('./datasets/Container_services/test/' + str(c) + '.csv', encoding="utf-8-sig", sep=';', index=False)
        print('The number of successfully generated containerized service data is: %d, which has been stored as file: %s.\n' \
              % (len(out_data[0]), './datasets/Container_services/' + str(c) + '.csv'))
