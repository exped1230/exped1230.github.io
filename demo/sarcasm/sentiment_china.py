import numpy as np
import matplotlib.pyplot as plt
import cv2
plt.rcParams["font.sans-serif"]=["Kaiti"] #设置字体
plt.rcParams["axes.unicode_minus"]=False
def img_rotate(src, angel):
    h,w = src.shape[:2]
    center = (w//2, h//2)
    M = cv2.getRotationMatrix2D(center, angel, 1.0)
    rotated_h = int((w * np.abs(M[0,1]) + (h * np.abs(M[0,0]))))
    rotated_w = int((h * np.abs(M[0,1]) + (w * np.abs(M[0,0]))))
    M[0,2] += (rotated_w - w) // 2
    M[1,2] += (rotated_h - h) // 2
    rotated_img = cv2.warpAffine(src, M, (rotated_w,rotated_h))

    return rotated_img
fig, ax = plt.subplots(figsize=(6,9), dpi=100)
# plt.figure(figsize=(6,8))
N = 2
ind = [0,0.6] 
# plt.xticks(ind, ('Image', 'Text'),fontsize=70,rotation=90)
# plt.yticks([0.35,0.82], ("Neg","Pos"),fontsize=70,rotation=90)
plt.xticks(ind, ('图像', '文本'),fontsize=70,rotation=90)
plt.yticks([0.4,0.85], ("积极","消极"),fontsize=70,rotation=90)

path = r"C:\Users\92056\Desktop\sarcasm629\jiaoben2304\chinese report\12\12_2\10_senti.png"
#          图  文
y=0.43
x=0.74
Bottom = (x,y)
Center = (1-x,1-y)

d = []
for i in range(0, len(Bottom)):
    sum = Bottom[i] + Center[i]
    d.append(sum)

width = 0.35  # 设置条形图一个长条的宽度
p1 = plt.bar(ind, Bottom, width, color='orange') 
p2 = plt.bar(ind, Center, width, bottom=Bottom,color='cornflowerblue')  
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)
plt.subplots_adjust(left=0.25,right=0.99,top=0.99,bottom=0.3)

plt.savefig(path)
img = cv2.imread(path)
img = img_rotate(img,-90)
cv2.imwrite(path,img[:,5:,:])
# plt.show()