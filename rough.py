import collections
import subprocess
import time
import threading

def read_output(process, append):
    for line in iter(process.stdout.readline, ""):
        append(line)

def main():
    # start process, redirect stdout
    process = subprocess.Popen(["top"], stdout=subprocess.PIPE, close_fds=True)
    try:
        # save last `number_of_lines` lines of the process output
        number_of_lines = 200
        q = collections.deque(maxlen=number_of_lines) # atomic .append()
        t = threading.Thread(target=read_output, args=(process, q.append))
        t.daemon = True
        t.start()

        #
        time.sleep(2)
    finally:
        process.terminate() #NOTE: it doesn't ensure the process termination

    # print saved lines
    print (q)

if __name__=="__main__":
    main()