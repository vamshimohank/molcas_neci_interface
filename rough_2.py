import time

file_name='o2.log'
f = open(file_name, 'r')

while True:

    line = f.readline()
    if not line :
        time.sleep(10)
        #print('Nothing New')
    else:
        if line == "PAUSED":
            print('MOLCAS ', line)
            exit()