res_path=r"C:\Users\92056\Desktop\infer_imgs\11\reses.txt"
data=[]
for line in  open(res_path,"r"):
    if line!="\n":
        data.append(eval(line))

idx=0
num=0
month='1'
file=open(r"C:\Users\92056\Desktop\sarcasm629\jiaoben2304\111.html","r", encoding="utf-8")
file2=open(r"C:\Users\92056\Desktop\sarcasm629\jiaoben2304\111_new.html","w", encoding="utf-8")
for line in file:
    # if "senti.png" in line:
    #     num=num+1
    #     front = line.split("<")[0]
    #     line = front+'<img src="chinese report\\9\\9_1\\' + str(num) + '_senti.png" width="240" height="140">'+'\n'
    if "neg_val_bar" in line:
        front = line.split("<")[0]
        line = front+'<div id="neg_val_bar" style="background:#DDDDDD; width:'+str(data[idx]/4)+'%;">'+'\n'
    if '<p id="neg_val" class="pl-5"' in line:
        front = line.split("<")[0]
        line = front+'<p id="neg_val" class="pl-5" style="font-size:25px;white-space:nowrap;">&#128533; 讽刺: '+str(format(data[idx],'.1f'))+'%</p>'+'\n'
    if "pos_val_bar" in line:
        front = line.split("<")[0]
        line = front+'<div id="pos_val_bar" style="background:#DDDDDD; width: '+str(25-(data[idx]/4))+'%;">'+'\n'
    if '<p id="pos_val" class="pl-5"' in line:
        front = line.split("<")[0]
        line = front+'<p id="pos_val" class="pl-5" style="font-size:25px;white-space:nowrap;">&#128512; 非讽刺: '+str(format(100-data[idx],'.1f'))+'%</p>'+'\n'
        idx+=1
        print(idx)
    file2.write(line)


num=0
file=open(r"C:\Users\92056\Desktop\sarcasm629\jiaoben2304\112.html","r", encoding="utf-8")
file2=open(r"C:\Users\92056\Desktop\sarcasm629\jiaoben2304\112_new.html","w", encoding="utf-8")
for line in file:
    # if "senti.png" in line:
    #     num=num+1
    #     front = line.split("<")[0]
    #     line = front+'<img src="chinese report\\5\\5_2\\' + str(num) + '_senti.png" width="240" height="140">'+'\n'
    if "neg_val_bar" in line:
        front = line.split("<")[0]
        line = front+'<div id="neg_val_bar" style="background:#DDDDDD; width:'+str(data[idx]/4)+'%;">'+'\n'
    if '<p id="neg_val" class="pl-5"' in line:
        front = line.split("<")[0]
        line = front+'<p id="neg_val" class="pl-5" style="font-size:25px;white-space:nowrap;">&#128533; 讽刺: '+str(format(data[idx],'.1f'))+'%</p>'+'\n'
    if "pos_val_bar" in line:
        front = line.split("<")[0]
        line = front+'<div id="pos_val_bar" style="background:#DDDDDD; width: '+str(25-(data[idx]/4))+'%;">'+'\n'
    if '<p id="pos_val" class="pl-5"' in line:
        front = line.split("<")[0]
        line = front+'<p id="pos_val" class="pl-5" style="font-size:25px;white-space:nowrap;">&#128512; 非讽刺: '+str(format(100-data[idx],'.1f'))+'%</p>'+'\n'
        idx+=1
        print(idx)
    file2.write(line)

num=0
file=open(r"C:\Users\92056\Desktop\sarcasm629\jiaoben2304\113.html","r", encoding="utf-8")
file2=open(r"C:\Users\92056\Desktop\sarcasm629\jiaoben2304\113_new.html","w", encoding="utf-8")
for line in file:
    # if "senti.png" in line:
    #     num=num+1
    #     front = line.split("<")[0]
    #     line = front+'<img src="chinese report\\5\\5_3\\' + str(num) + '_senti.png" width="240" height="140">'+'\n'
    if "neg_val_bar" in line:
        front = line.split("<")[0]
        line = front+'<div id="neg_val_bar" style="background:#DDDDDD; width:'+str(data[idx]/4)+'%;">'+'\n'
    if '<p id="neg_val" class="pl-5"' in line:
        front = line.split("<")[0]
        line = front+'<p id="neg_val" class="pl-5" style="font-size:25px;white-space:nowrap;">&#128533; 讽刺: '+str(format(data[idx],'.1f'))+'%</p>'+'\n'
    if "pos_val_bar" in line:
        front = line.split("<")[0]
        line = front+'<div id="pos_val_bar" style="background:#DDDDDD; width: '+str(25-(data[idx]/4))+'%;">'+'\n'
    if '<p id="pos_val" class="pl-5"' in line:
        front = line.split("<")[0]
        line = front+'<p id="pos_val" class="pl-5" style="font-size:25px;white-space:nowrap;">&#128512; 非讽刺: '+str(format(100-data[idx],'.1f'))+'%</p>'+'\n'
        idx+=1
        print(idx)
    file2.write(line)


num=0
file=open(r"C:\Users\92056\Desktop\sarcasm629\jiaoben2304\114.html","r", encoding="utf-8")
file2=open(r"C:\Users\92056\Desktop\sarcasm629\jiaoben2304\114_new.html","w", encoding="utf-8")
for line in file:
    # if "senti.png" in line:
    #     num=num+1
    #     front = line.split("<")[0]
    #     line = front+'<img src="chinese report\\5\\5_4\\' + str(num) + '_senti.png" width="240" height="140">'+'\n'
    if "neg_val_bar" in line:
        front = line.split("<")[0]
        line = front+'<div id="neg_val_bar" style="background:#DDDDDD; width:'+str(data[idx]/4)+'%;">'+'\n'
    if '<p id="neg_val" class="pl-5"' in line:
        front = line.split("<")[0]
        line = front+'<p id="neg_val" class="pl-5" style="font-size:25px;white-space:nowrap;">&#128533; 讽刺: '+str(format(data[idx],'.1f'))+'%</p>'+'\n'
    if "pos_val_bar" in line:
        front = line.split("<")[0]
        line = front+'<div id="pos_val_bar" style="background:#DDDDDD; width: '+str(25-(data[idx]/4))+'%;">'+'\n'
    if '<p id="pos_val" class="pl-5"' in line:
        front = line.split("<")[0]
        line = front+'<p id="pos_val" class="pl-5" style="font-size:25px;white-space:nowrap;">&#128512; 非讽刺: '+str(format(100-data[idx],'.1f'))+'%</p>'+'\n'
        idx+=1
        print(idx)
    file2.write(line)