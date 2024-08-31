import csv

# 定义生成的CSV文件的文件名
filename = "../../datasets/host_positions.csv"

# 定义空间的尺寸
space_size = 4

# 初始化一个空列表来存储坐标
positions = []

# 生成4x4空间内的16个顶点坐标
for x in range(space_size):
    for y in range(space_size):
        positions.append((x, y))

# 将坐标写入CSV文件
with open(filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["x", "y"])  # 写入表头
    writer.writerows(positions)  # 写入所有的坐标数据

print(f"CSV file '{filename}' has been created with host positions.")