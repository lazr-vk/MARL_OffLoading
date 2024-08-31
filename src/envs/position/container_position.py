import csv
import random

# 定义4x4的空间
space_size = 4
num_containers = 16
# 随机生成三个容器任务的坐标
tasks = [(random.uniform(0, space_size), random.uniform(0, space_size)) for _ in range(num_containers)]

# 写入CSV文件
with open('../../datasets/container_tasks.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['x', 'y'])  # 写入表头
    writer.writerows(tasks)  # 写入任务坐标

print("CSV file with container task coordinates generated successfully.")
