import matplotlib.pyplot as plt
import numpy as np
x_data = ['Neg', "Pos"]
y1 = np.array([1,2])
data = [0.2,0.8]
plt.rcParams["font.family"] = "Times New Roman"
bar_width=0.25
plt.bar(x=[0.15,0.9], height=data,
 label='fbgggggg', color=['b','r'], alpha=0.8, width=0.45)
for x, y in enumerate([0,1], y1):
    plt.text(x, y + 0.1, y, ha='center', va='bottom')
x = np.array(list(range(2)))
# y = np.array((0,1))
# plt.yticks(y,fontsize=30)
plt.xticks([0.15,0.9],['Neg', "Pos"],fontsize=30)
plt.show()