import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import matplotlib.gridspec as gridspec

# Load the data from the JSON file
# with open('../results/sacred/54/info.json', 'r') as f:
with open('../results/offloading/430/info.json', 'r') as f:
    data = json.load(f)

# Extract the x and y values for 'battle_won_mean', 'test_battle_won_mean', and 'loss'
critic_loss = []
test_battle_won_mean = []
pg_loss = []
return_mean = []
for i, val in enumerate(data['critic_loss']):
    critic_loss.append([i + 1, val])
# for i, val in enumerate(data['test_battle_won_mean']):
#     test_battle_won_mean.append([i + 1, val])
# for i, val in enumerate(data['pg_loss']):
for i, val in enumerate(data['pg_loss']):
    pg_loss.append([i + 1, val])
for rm in data['return_mean']:
    return_mean.append(rm['value'])

# Set up the layout of the subplots
til = input("实验名称：\n")  # 输入本次实验的编号或者名称
fig = plt.figure(figsize=(10, 8))
gs = gridspec.GridSpec(nrows=3, ncols=1, height_ratios=[1, 1, 1.2])
gs.update(hspace=0.5, wspace=0.5)
fig.suptitle(til, fontsize=16)

# Create the plot for battle_won_mean and test_battle_won_mean
ax1 = plt.subplot(gs[0])
ax1.plot(*zip(*critic_loss), label='battle_won_mean')
# ax1.plot(*zip(*test_battle_won_mean), label='test_battle_won_mean')
ax1.grid()
# ax1.set_ylim(0, 30.0)
ax1.autoscale(axis='y')
# Add labels and title to the plot
ax1.set_xlabel('Index')
ax1.set_ylabel('Value')
ax1.set_title('critic_loss')

# Add legend to the plot
ax1.legend()

# Set y-axis tick interval to 0.2
ax1.xaxis.set_major_locator(MultipleLocator(100))
# ax1.yaxis.set_major_locator(MultipleLocator(1000))

# Create the plot for loss
ax2 = plt.subplot(gs[1])
ax2.plot(*zip(*pg_loss), label='loss')

# Add labels and title to the plot
ax2.set_xlabel('episode')
ax2.set_ylabel('Value')
ax2.set_title('pg_loss')

# Add legend to the plot
ax2.legend()

# Set x-axis tick interval to 25
ax2.xaxis.set_major_locator(MultipleLocator(100))
ax2.autoscale(axis='y')
# ax2.yaxis.set_major_locator(MultipleLocator(50))
# Add grid lines to both plots
ax2.grid()

# Create the plot for return_mean
ax3 = plt.subplot(gs[2])
ax3.plot(return_mean)
ax3.grid()

# Add labels and title to the plot
ax3.set_xlabel('episode')
ax3.set_ylabel('Value')
ax3.set_title('Return_Mean')

# Set x-axis tick interval to 25
ax3.xaxis.set_major_locator(MultipleLocator(100))
# ax3.yaxis.set_major_locator(MultipleLocator(50))
ax3.autoscale(axis='y')
# ax3.xaxis.set_major_locator(md.HourLocator(interval=5))
# Save the plot to the output directory
plt.savefig("存放图像的地址" + til + '.png')

# display the picture
plt.show()
