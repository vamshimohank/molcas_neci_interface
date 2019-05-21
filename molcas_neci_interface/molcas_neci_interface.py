from __future__ import print_function
import sys, shutil, os
from typing import BinaryIO

import subprocess
import time

os.environ['PYTHONWARNINGS'] = "ignore"

if not sys.warnoptions:
    import os, warnings

    warnings.simplefilter("default")  # Change the filter in this process
    os.environ["PYTHONWARNINGS"] = "ignore"


def if_file_exists_in_remote(remote_ip, file_name_with_full_path):
    from paramiko_helper.ssh_helper import SFTPHelper
    import os
    try :
        user = os.getenv('USER')
        password = os.getenv('PASSWORD')

        c=SFTPHelper()
        ssh_args={"password":password, "username": user, "auth_timeout": 3600.0, "banner_timeout": 3600.0, "timeout": 3600.0}
        c.connect(remote_ip,**ssh_args)
        if c.exists(file_name_with_full_path):
            c.close()
            return True
        else:
            c.close()
            return False
    except KeyboardInterrupt:
        exit()

def reread_inp():
    print("Reread the input parameters")


def activate_molcas():
    molcas_WorkDir = os.getenv('MOLCAS_WorkDir')
    f = open(molcas_WorkDir + 'neci.out')
    string = 'REDUCED DENSITY MATRICES'
    for line in f.readlines():
        if string in line:
            E = line.split()[8]
            try:
                print('CASCI E = ', E)
            except UnboundLocalError:
                print("Although the RDMs are found, there is no Energy printed in the NECI out file.\n"
                      "Looks like that NECI did not finish clean. Please check the NECI out file")
                print("Exiting the program: please restart MOLCAS with the lastest orbitals to continue the CASSCF\n "
                      "calculation")
                exit()
            # return E
            break
    f.close()
    f = open(molcas_WorkDir + "NEWCYCLE", 'w+')  # type: file
    f.write(E)
    f.close()
    return None


def replace_definedet(project):
    molcas_WorkDir = os.getenv('MOLCAS_WorkDir')
    f = open(molcas_WorkDir + 'neci.out')
    definedet=''
    for line in f.readlines():
        if 'definedet' in line:
            definedet = line
            # print(definedet)
    f.close()

    neci_inp_file_path = molcas_WorkDir + project + '.FciInp'
    import fileinput
    for line in fileinput.FileInput(neci_inp_file_path, inplace=1):
        # if "calc" in line:
        if len(line.split()) == 1 and 'calc' in line.split()[0][:4]:
            line = line.replace(line, line + definedet+'\n')
        print(line, end='')


def copy_to_molcas_workdir(project, neci_scratch_dir):
    cmd = "scp allogin2.fkf.mpg.de:" + neci_scratch_dir + '/TwoRDM* ./tmp/'
    subprocess.call("%s" % cmd, shell=True)
    cmd = "scp allogin2.fkf.mpg.de:" + neci_scratch_dir + '/out .'
    subprocess.call("%s" % cmd, shell=True)


def copy_to_main_dir(project, neci_scratch_dir):
    shutil.copyfile(os.path.join(neci_scratch_dir, 'TwoRDM_abab.1'), './' + project + '.TwoRDM_abab')
    shutil.copyfile(os.path.join(neci_scratch_dir, 'TwoRDM_abba.1'), './' + project + '.TwoRDM_abba')
    shutil.copyfile(os.path.join(neci_scratch_dir, 'OneRDM.1'), './' + project + '.OneRDM')


def run_neci_on_remote(project,iter):
    from fabric import Connection

    import sys,os

    if not sys.warnoptions:
        import os, warnings
        warnings.simplefilter("ignore")  # Change the filter in this process
        os.environ["PYTHONWARNINGS"] = "default"

    remote_ip = os.getenv('REMOTE_MACHINE_IP')
    remote_WorkDir = os.getenv('REMOTE_NECI_WorkDir')
    molcas_WorkDir = os.getenv('MOLCAS_WorkDir')
    CurrDir = os.getenv('CurrDir')
    user = os.getenv('USER')
    neci_job_script = os.getenv('NECI_JOB_SCRIPT')
    job_folder = str(os.getpid())
    neci_WorkDir = remote_WorkDir + job_folder + '/'

    # replace the definedet line in the neci input
    if iter >= 1:
        replace_definedet(project)

    # c = Connection(remote_ip, user=user)
    user = os.getenv('USER')
    password = os.getenv('PASSWORD')
    c = Connection(remote_ip, user=user, connect_kwargs={"password": password})

    print('Transferring FciInp and FciDmp to the remote computer {0}:{1}'.format(remote_ip, neci_WorkDir))

    if not if_file_exists_in_remote(remote_ip, neci_WorkDir):
        c.run('mkdir {0}'.format(neci_WorkDir))
    c.put(molcas_WorkDir + '/' + project + '.FciInp', remote=neci_WorkDir)
    c.put(molcas_WorkDir + '/' + project + '.FciDmp', remote=neci_WorkDir)
    c.put(CurrDir + '/' + neci_job_script, remote=neci_WorkDir)

    print("Submiting the job to the queue ...")

    with c.cd(neci_WorkDir):
        if os.getenv('scheduler') == 'llq':
            job_submit_line = c.run('llsubmit {0}'.format(neci_job_script))
        elif os.getenv('scheduler') == 'slurm':
            job_submit_line = c.run('sbatch {0}'.format(neci_job_script))
    job_id = job_submit_line.stdout.split()[3]

    c.close()
    return job_id


def check_if_neci_completed(neci_work_dir, job_id, interactive):
    from time import sleep
    from datetime import datetime
    from fabric import Connection
    remote_ip = os.getenv('REMOTE_MACHINE_IP')
    user = os.getenv('USER')
    password = os.getenv('PASSWORD')
    c = Connection(remote_ip, user=user, connect_kwargs={"password": password})
    # c = Connection(remote_ip)
    if not interactive:
        if os.getenv('scheduler') == "llq":
            result = c.run('llq -j {0}'.format(job_id))
            try:
                status = result.stdout.split()[19]
            except IndexError:
                status = 'U'
        elif os.getenv('scheduler') == "slurm":
            result = c.run('squeue -j {0}'.format(job_id))
            try:
                status = result.stdout.split()[4]
            except IndexError:
                status = 'U'
        if status == 'U':
            print('Cannot find job with {0} in the queue'.format(job_id))
            print("Job either completed or got killed immediately. Will take it as completed ..")
            status = "C"
        if status != "R" and status != "C":
            while status != "R" and status != "C":
                if status == "I" or status == "PD":
                    print('Job waiting in queue')
                sleep(10)
                try:
                    if os.getenv('scheduler') == "llq":
                        result = c.run('llq -j {0} '.format(job_id))
                        status = result.stdout.split()[19]
                    if os.getenv('scheduler') == "slurm":
                        result = c.run('squeue -j {0} '.format(job_id))
                        status = result.stdout.split()[12]
                except IndexError:
                    print('Cannot find job with {0} in the queue'.format(job_id))
                    print("Job either completed or got killed immediately. Will take it as completed ..")
                    status = "C"
            c.close()
        # print('Job running ... ')
        # print('NECI is running: {0}'.format(datetime.now()))
        elif status == "R":
            print('Job is running! will wait for {} minutes for it to complete'.format(int(os.getenv('neci_exec_time'))))
            sleep(float(os.getenv('neci_exec_time')))
        else:
            print('checking if RDMs are created ....')
    else:
        print('checking if RDMs are created ....')

    # file_name_with_full_path = neci_work_dir + 'TwoRDM_aaaa.1'

    while not if_file_exists_in_remote(remote_ip, neci_work_dir + 'TwoRDM_aaaa.1'):
        sleep(20)
    # if if_file_exists_in_remote(remote_ip, file_name_with_full_path):
    print('NECI created RDMs, transfering to MOLCAS work directory ')

    return True


def get_rdms_from_neci(iter, job_folder):
    from fabric import Connection
    remote_ip = os.getenv('REMOTE_MACHINE_IP')
    user = os.getenv('USER')
    password = os.getenv('PASSWORD')
    # print(password)
    c = Connection(remote_ip, user=user, connect_kwargs={"password": password})

    molcas_WorkDir = os.getenv('MOLCAS_WorkDir')
    remote_WorkDir = os.getenv('REMOTE_NECI_WorkDir')
    neci_WorkDir = remote_WorkDir + job_folder + '/'
    print('Copying RDMs and NECI output from {} to {}'.format(neci_WorkDir,molcas_WorkDir))
    # print(neci_WorkDir)
    # print(' to ')
    # print(molcas_WorkDir)
    c.get(neci_WorkDir + 'TwoRDM_aaaa.1', local=molcas_WorkDir + 'TwoRDM_aaaa.1')  # ,local=molcas_WorkDir)
    c.get(neci_WorkDir + 'TwoRDM_abab.1', local=molcas_WorkDir + 'TwoRDM_abab.1')
    c.get(neci_WorkDir + 'TwoRDM_abba.1', local=molcas_WorkDir + 'TwoRDM_abba.1')
    c.get(neci_WorkDir + 'TwoRDM_bbbb.1', local=molcas_WorkDir + 'TwoRDM_bbbb.1')
    c.get(neci_WorkDir + 'TwoRDM_baba.1', local=molcas_WorkDir + 'TwoRDM_baba.1')
    c.get(neci_WorkDir + 'TwoRDM_baab.1', local=molcas_WorkDir + 'TwoRDM_baab.1')
    time.sleep(10)
    c.get(neci_WorkDir + 'out', local=molcas_WorkDir + 'neci.out')
    # iter=0
    with c.cd(neci_WorkDir):
        iter_folder = 'Iter_' + str(iter)
        c.run('mkdir {0}'.format(iter_folder))
        c.run('mv TwoRDM* {0}'.format(iter_folder))
        c.run('mv out {0}/neci.out'.format(iter_folder))
        c.run('mv input {0}/neci.inp'.format(iter_folder))
        c.run('cp FCIMCStats {0}/.'.format(iter_folder))
        c.run('tar -cf {0}.tar.gz {0}'.format(iter_folder, iter_folder))
    c.get(neci_WorkDir + iter_folder + '.tar.gz', local=molcas_WorkDir + iter_folder + '.tar.gz')
    # c.run('rm -r {0}'.format(neci_WorkDir))
    c.close()
    # c.run('rm TwoRDM*')
    # iter += 1



def executeMolcas(inp_file):
    import os
    try:
        cmd = "pymolcas -new -f -b1 "
        molcas_process = subprocess.Popen("%s  %s " % (cmd, inp_file), shell=True, close_fds=True,
                                          preexec_fn=os.setsid)
        print('MOLCAS running ...')
    except subprocess.CalledProcessError as err:
        raise err
    return molcas_process

def check_if_molcas_paused(out_file,molcas_runtime=20):
    time.sleep(molcas_runtime)
    f = open(out_file, 'r')
    line_temp = ''
    while True:
        line = f.readline()
        if not line:
            time.sleep(molcas_runtime)
        else:
            if len(line.split()) != 0 and line.split()[0] == "PAUSED":
                # molcas_WorkDir = line_temp.split()[0]
                print('MOLCAS paused and files for NECI are produced', )
                f.close()
                return True
            else:
                pass

def analyse_neci():
    import subprocess
    import tarfile
    import numpy as np

    iter = 0
    tar = tarfile.open("Iter_" + str(iter) + '.tar.gz', "r:gz")
    FCIMCstats = tar.ge

    print("Analyzing NECI output")
    molcas_WorkDir = os.getenv('MOLCAS_WorkDir')
    plot_script = input('Enter the python plotting program')
    subprocess.Popen('python', plot_script)


if __name__ == '__main__':
    project = 'ls'
    neci_scratch_dir = '/home/katukuri/work/Molcas/NiO/cas24in27/non-emb/NECI'
    neci_out_file = 'out'
    copy_to_molcas_workdir(project, neci_scratch_dir)

    E = get_e(neci_out_file)
    print(E)
