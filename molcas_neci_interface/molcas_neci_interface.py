from __future__ import print_function

import os
import subprocess
import sys
import time

from logger import *

from molcas_neci_interface import logger

os.environ['PYTHONWARNINGS'] = "ignore"

if not sys.warnoptions:
    import os, warnings

    warnings.simplefilter("default")  # Change the filter in this process
    os.environ["PYTHONWARNINGS"] = "ignore"

def if_file_exists_in_remote(remote_ip, file_name_with_full_path):
    from paramiko_helper.ssh_helper import SFTPHelper
    import os
    try:
        user = os.getenv('USER')
        password = os.getenv('PASSWORD')

        c = SFTPHelper()
        ssh_args = {"password": password, "username": user, "auth_timeout": 7600.0, "banner_timeout": 7600.0,
                    "timeout": 7600.0}
        c.connect(remote_ip, **ssh_args)
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
    logger.info("Reread the input parameters")


def activate_molcas():
    molcas_WorkDir = os.getenv('MOLCAS_WorkDir')
    f = open(os.path.join(molcas_WorkDir , 'neci.out'))
    string = 'REDUCED DENSITY MATRICES'
    for line in f.readlines():
        if string in line:
            E = line.split()[8]
            try:
                print('CASCI E = ', E)
                logger.info('CASCI E = {0}'.format(E))
            except UnboundLocalError:
                print("Although the RDMs are found, there is no Energy printed in the NECI out file.\n"
                      "Looks like that NECI did not finish clean. Please check the NECI out file")
                logger.info("Although the RDMs are found, there is no Energy printed in the NECI out file.\n"
                      "Looks like that NECI did not finish clean. Please check the NECI out file")
                print("Exiting the program: please restart MOLCAS with the lastest orbitals to continue the CASSCF\n "
                      "calculation")
                logger.info("Exiting the program: please restart MOLCAS with the lastest orbitals to continue the CASSCF\n "
                      "calculation")
                exit()
            # return E
            break
    f.close()
    f = open(os.path.join(molcas_WorkDir , "NEWCYCLE"), 'w+')  # type: file
    f.write(E)
    f.close()
    return None


def replace_definedet(project):
    molcas_WorkDir = os.getenv('MOLCAS_WorkDir')
    f = open(os.path.join(molcas_WorkDir , 'neci.out'))
    definedet = ''
    for line in f.readlines():
        if 'definedet' in line:
            definedet = line
            # print(definedet)
    f.close()

    import fileinput
    neci_inp_file_path = os.path.join(molcas_WorkDir , 'neci.inp')

    for line in fileinput.FileInput(neci_inp_file_path, inplace=1):
        # if "calc" in line:

        if len(line.split()) != 0 and 'definedet' in line.split()[0]:
            line = line.replace(line, definedet + '\n')

        elif len(line.split()) == 1 and 'calc' in line.split()[0][:4]:
            line = line.replace(line, line + definedet + '\n')

        print(line, end='')


def run_neci_on_remote(project, iter):
    from fabric import Connection

    import sys, os

    if not sys.warnoptions:
        import warnings
        warnings.simplefilter("ignore")  # Change the filter in this process
        os.environ["PYTHONWARNINGS"] = "default"

    remote_ip = os.getenv('REMOTE_MACHINE_IP')
    molcas_WorkDir = os.getenv('MOLCAS_WorkDir')
    neci_WorkDir = os.getenv('REMOTE_NECI_WorkDir')
    CurrDir = os.getenv('CurrDir')
    user = os.getenv('USER')
    neci_job_script = os.getenv('NECI_JOB_SCRIPT')

    # replace the definedet line in the neci input
    if iter >= 1:
        replace_definedet(project)

    # c = Connection(remote_ip, user=user)
    user = os.getenv('USER')
    password = os.getenv('PASSWORD')
    c = Connection(remote_ip, user=user, connect_kwargs={"password": password})

    print('Transferring FciInp and FciDmp to the remote computer {0}:{1}'.format(remote_ip, neci_WorkDir))
    logger.info('Transferring FciInp and FciDmp to the remote computer {0}:{1}'.format(remote_ip, neci_WorkDir))

    if not if_file_exists_in_remote(remote_ip, neci_WorkDir):
        c.run('mkdir {0}'.format(neci_WorkDir))

    if iter >= 1:
        c.put(os.path.join(molcas_WorkDir , 'neci.inp'), remote = os.path.join(neci_WorkDir , 'input'))
    else:
        c.put(os.path.join(molcas_WorkDir , project + '.FciInp'), remote = neci_WorkDir)

    c.put(os.path.join(molcas_WorkDir , project + '.FciDmp'), remote = neci_WorkDir)
    c.put(os.path.join(CurrDir , neci_job_script), remote = neci_WorkDir)

    print("Submiting the job to the queue ...")
    logger.info("Submiting the job to the queue ...")

    with c.cd(neci_WorkDir):
        if os.getenv('scheduler') == 'llq':
            job_submit_line = c.run('llsubmit {0}'.format(neci_job_script))
        elif os.getenv('scheduler') == 'slurm':
            job_submit_line = c.run('sbatch {0}'.format(neci_job_script))
    job_id = job_submit_line.stdout.split()[3]

    c.close()
    return job_id

def stop_pymolcas():
    logger.info('killing pymolcas')
    os.killpg(os.getpgid(molcas_process.pid), signal.SIGTERM)



def read_interrupt_inp(reason="INTERRUPT"):
    import signal
    if reason == "INTERRUPT":
        try:
            f = open(os.getenv('CurrDir') + '/INTERRUPT', 'r')
            print('Interrupted! what would you like to do?')
            logger.info('Interrupted! what would you like to do?')
            os.remove(os.getenv('CurrDir') + '/INTERRUPT')
            while True:
                inp_molcas_run = input("(a) Abort MOLCAS ?  \n"
                                       "(b) Continue \n"
                                       "(c) more options to come \n")

                if inp_molcas_run.split()[0].lower() == 'a':
                    os.killpg(os.getpgid(molcas_process.pid), signal.SIGTERM)
                    exit()
                elif inp_molcas_run.split()[0].lower() == 'b':
                    break
                else:
                    print('Wrong option! Try again..\n')
                    logger.info('Wrong option! Try again..\n')
            f.close()
        except FileNotFoundError:
            pass
    elif reason == "CONTINUE":
        try:
            f = open(os.getenv('CurrDir') + '/CONTINUE', 'r')
            print("You said the job started running...")
            logger.info("You said the job started running...")
            f.close()
            os.remove((os.getenv('CurrDir') + '/CONTINUE'))
            return True
        except:
            pass


def check_if_neci_completed(neci_work_dir, job_id, interactive):
    from time import sleep
    from fabric import Connection
    remote_ip = os.getenv('REMOTE_MACHINE_IP')
    user = os.getenv('USER')
    password = os.getenv('PASSWORD')
    if not interactive:
        if os.getenv('scheduler') == "llq":
            c = Connection(remote_ip, user=user, connect_kwargs={"password": password})
            result = c.run('llq -j {0}'.format(job_id))
            c.close()
            try:
                status = result.stdout.split()[19]
            except IndexError:
                status = 'U'
        elif os.getenv('scheduler') == "slurm":
            c = Connection(remote_ip, user=user, connect_kwargs={"password": password})
            result = c.run('squeue -j {0}'.format(job_id))
            c.close()
            try:
                status = result.stdout.split()[4]
            except IndexError:
                status = 'U'
        if status == 'U':
            print('Cannot find job with {0} in the queue'.format(job_id))
            logger.info('Cannot find job with {0} in the queue'.format(job_id))
            print("Job either completed or got killed immediately. Will take it as completed ..")
            logger.info("Job either completed or got killed immediately. Will take it as completed ..")
            status = "C"
        if status != "R" and status != "C":
            while status != "R" and status != "C":
                if status == "I" or status == "PD":
                    print('Job waiting in queue, will check again every 2 min ')
                    logger.info('Job waiting in queue, will check again every 5 min ')
                    print('If you find the job running, creat an empty file with name "CONTINUE"')
                    logger.info('If you find the job running, creat an empty fill with name "CONTINUE"')
                    try:
                        for i in range(60):
                            running = read_interrupt_inp(reason="CONTINUE")
                            if running:
                                status = "R"
                                break
                            else:
                                sleep(1)
                    except KeyboardInterrupt:
                        break
                try:
                    if os.getenv('scheduler') == "llq":
                        c = Connection(remote_ip, user=user, connect_kwargs={"password": password})
                        result = c.run('llq -j {0} '.format(job_id))
                        c.close()
                        status = result.stdout.split()[19]
                    if os.getenv('scheduler') == "slurm":
                        c = Connection(remote_ip, user=user, connect_kwargs={"password": password})
                        result = c.run('squeue -j {0} '.format(job_id))
                        status = result.stdout.split()[12]
                        c.close()
                except IndexError:
                    print('Cannot find job with {0} in the queue'.format(job_id))
                    logger.info('Cannot find job with {0} in the queue'.format(job_id))
                    print("Job either completed or got killed immediately. Will take it as completed ..")
                    logger.info("Job either completed or got killed immediately. Will take it as running ..")
                    status = "C"
            if status != "C":
                print('Job is running ... ')
                logger.info('Job is running!')

                print('Waiting for an estimated {0} seconds for NECI to produce RDMs'
                    .format(float(os.getenv('neci_exec_time'))))
                logger.info('Waiting for an estimated {0} seconds for NECI to produce RDMs'
                            .format(float(os.getenv('neci_exec_time'))))
            # time.sleep(float(os.getenv('neci_exec_time')))
                wait_time = float(os.getenv('neci_exec_time'))
                for t in range(60):
                    try:
                        time.sleep(wait_time/60)
                    # print('Elapsed time : {:05.3f}'.format(t*(wait_time/60)), end="\r")
                        print('Waiting for : {:05.3f} seconds'.format(wait_time - t*(wait_time/60)), end="\r")
                    except KeyboardInterrupt:
                        break
                print('checking if RDMs are created ....')
                logger.info('checking if RDMs are created ....')
        # print('NECI is running: {0}'.format(datetime.now()))
            else:
                print('Job canceled ')
                logger.info('Job is canceled!')
                print("check the reason for the reason and resubmit the calcualtion on the remote")
                try:
                    while True:
                        status = input("Press R if the new job is submitted and running or just to continue\n")
                        if status.lower() == "r":
                            status = "R"
                            print('Job is running!') 
                            logger.info('Job is running!') 
                            print('Waiting for an estimated {0} seconds for NECI to produce RDMs'
                                  .format(float(os.getenv('neci_exec_time'))))
                            logger.info('Waiting for an estimated {0} seconds for NECI to produce RDMs'
                                  .format(float(os.getenv('neci_exec_time'))))
                            wait_time = float(os.getenv('neci_exec_time'))
                            for t in range(60):
                                try:
                                    time.sleep(wait_time/60)
                                    print('Waiting for : {:05.3f} seconds'.format(wait_time - t*(wait_time/60)), end="\r")
                                except KeyboardInterrupt:
                                    break
                            print('checking if RDMs are created ....')
                            logger.info('checking if RDMs are created ....')
                            break
                        else:
                            print("Wrong choice! Try again")
                except KeyboardInterrupt:
                    logger.info('killing pymolcas')
                    os.killpg(os.getpgid(molcas_process.pid), signal.SIGTERM)
        elif status == "R":
            print('Job is running!') 
            logger.info('Job is running!') 
            print('Waiting for an estimated {0} seconds for NECI to produce RDMs'
                  .format(float(os.getenv('neci_exec_time'))))
            logger.info('Waiting for an estimated {0} seconds for NECI to produce RDMs'
                  .format(float(os.getenv('neci_exec_time'))))
            wait_time = float(os.getenv('neci_exec_time'))
            for t in range(60):
                try:
                    time.sleep(wait_time/60)
                    print('Waiting for : {:05.3f} seconds'.format(wait_time - t*(wait_time/60)), end="\r")
                except KeyboardInterrupt:
                    break
            print('checking if RDMs are created ....')
            logger.info('checking if RDMs are created ....')
        else:
            print('checking if RDMs are created ....')
            logger.info('checking if RDMs are created ....')
    else:
        if status != "C":
            print('checking if RDMs are created ....')
            logger.info('checking if RDMs are created ....')

    # file_name_with_full_path = neci_work_dir + 'TwoRDM_aaaa.1'

    while not if_file_exists_in_remote(remote_ip, neci_work_dir + 'TwoRDM_aaaa.1'):
        wait_time = 30
        for t in range(60):
            try:
                time.sleep(wait_time/60)
                read_interrupt_inp()
                # print('Waiting for : {:4.3f}'.format(t*(wait_time/60)), end="\r")
                # print('Waiting for : {:05.3f} seconds'.format(wait_time - t*(wait_time/60)), end="\r")
            except KeyboardInterrupt:
                break
        read_interrupt_inp()
    # if if_file_exists_in_remote(remote_ip, file_name_with_full_path):
    print('NECI created RDMs, transfering to MOLCAS work directory ')
    logger.info('NECI created RDMs, transfering to MOLCAS work directory ')

    return True


def get_rdms_from_neci(iter):
    from fabric import Connection
    remote_ip = os.getenv('REMOTE_MACHINE_IP')
    user = os.getenv('USER')
    password = os.getenv('PASSWORD')
    # print(password)
    c = Connection(remote_ip, user=user, connect_kwargs={"password": password})

    molcas_WorkDir = os.getenv('MOLCAS_WorkDir')
    neci_WorkDir = os.getenv('REMOTE_NECI_WorkDir')
    print('Copying RDMs and NECI output from {} to {}'.format(neci_WorkDir, molcas_WorkDir))
    logger.info('Copying RDMs and NECI output from {} to {}'.format(neci_WorkDir, molcas_WorkDir))
    # print(neci_WorkDir)
    # print(' to ')
    # print(molcas_WorkDir)
    c.get(os.path.join(neci_WorkDir , 'TwoRDM_aaaa.1'), local = os.path.join(molcas_WorkDir , 'TwoRDM_aaaa.1'))  # ,local=molcas_WorkDir)
    c.get(os.path.join(neci_WorkDir , 'TwoRDM_abab.1'), local = os.path.join(molcas_WorkDir , 'TwoRDM_abab.1'))  # ,local=molcas_WorkDir)
    c.get(os.path.join(neci_WorkDir , 'TwoRDM_bbbb.1'), local = os.path.join(molcas_WorkDir , 'TwoRDM_bbbb.1'))  # ,local=molcas_WorkDir)
    c.get(os.path.join(neci_WorkDir , 'TwoRDM_abba.1'), local = os.path.join(molcas_WorkDir , 'TwoRDM_abba.1'))  # ,local=molcas_WorkDir)
    c.get(os.path.join(neci_WorkDir , 'TwoRDM_baba.1'), local = os.path.join(molcas_WorkDir , 'TwoRDM_baba.1'))  # ,local=molcas_WorkDir)
    c.get(os.path.join(neci_WorkDir , 'TwoRDM_baab.1'), local = os.path.join(molcas_WorkDir , 'TwoRDM_baab.1'))  # ,local=molcas_WorkDir)
    time.sleep(3)
    c.get(os.path.join(neci_WorkDir , 'out'), local = os.path.join(molcas_WorkDir , 'neci.out'))
    c.get(os.path.join(neci_WorkDir , 'input'), local = os.path.join(molcas_WorkDir , 'neci.inp'))
    # iter=0
    with c.cd(neci_WorkDir):
        iter_folder = 'NECI_iter_' + str(iter)
        c.run('mkdir {0}'.format(iter_folder))
        c.run('mv TwoRDM* {0}'.format(iter_folder))
        c.run('mv out {0}/neci.out'.format(iter_folder))
        c.run('mv input {0}/neci.inp'.format(iter_folder))
        c.run('mv FCIMCStats {0}/.'.format(iter_folder))
        c.run('mv INITIATORStats {0}/.'.format(iter_folder))
        c.run('mv FCIDUMP {0}/.'.format(iter_folder))
        c.run('mv NO_OCC_NUMEBRS.1 {0}/.'.format(iter_folder))
        c.run('mv OneRDM.1 {0}/.'.format(iter_folder))
        c.run('mv RDMEstimates {0}/.'.format(iter_folder))
        c.run('mv popsfile.h5 {0}/.'.format(iter_folder))
#        c.run('mv Blocks* {0}/.'.format(iter_folder))
        c.run('tar -cf {0}.tar.gz {0}'.format(iter_folder, iter_folder))
#    if not os.path.isfile(os.path.join(os.getenv('CurrDir'),'NECI_files')):
#	logger.info('NECI_files folder doesnot exist')
#        os.mkdir(os.path.join(os.getenv('CurrDir'),'NECI_files'))
#    else:
#	logger.info('NECI_files folder exists, removing it!')
#        shutil.rmtree(os.getenv('CurrDir'),'NECI_files')
#        os.mkdir(os.path.join(os.getenv('CurrDir'),'NECI_files'))
#    c.get(os.path.join(neci_WorkDir , iter_folder + '.tar.gz'), local = os.path.join(os.getenv('CurrDir') , os.path.join('NECI_files',iter_folder + '.tar.gz')))
#    c.get(os.path.join(neci_WorkDir , 'FCIMCStats'), local = os.path.join(os.getenv('CurrDir') , 'FCIMCStats.' + str(iter)))
    c.get(os.path.join(neci_WorkDir , iter_folder + '.tar.gz'), local = os.path.join(os.getenv('CurrDir'), iter_folder + '.tar.gz'))
    #c.run('rm -r {0}'.format(neci_WorkDir))
    c.close()
    # c.run('rm TwoRDM*')
    # iter += 1


def executeMolcas(inp_file):
    import os
    try:
        cmd = "pymolcas -new -f -b1 "
        molcas_process = subprocess.Popen("%s  %s " % (cmd, inp_file), shell=True, close_fds=True,
                                          preexec_fn=os.setsid)
    except subprocess.CalledProcessError as err:
        raise err
    return molcas_process


def check_if_molcas_paused(out_file, molcas_runtime=10):
    time.sleep(molcas_runtime)
    f = open(out_file, 'r')
    while True:
        line = f.readline()
        if not line:
            time.sleep(molcas_runtime)
        else:
            if len(line.split()) != 0 and line.split()[0] == "PAUSED":
                print('MOLCAS paused and files for NECI are produced', )
                logger.info('MOLCAS paused and files for NECI are produced', )
                f.close()
                return True
            elif len(line.split()) != 0 and line.split()[0] == "Error:":
                print('Something is wrong with MOLCAS run, please check the corresponding output', )
                logger.info('Something is wrong with MOLCAS run, please check the corresponding output', )
                print('Killing pymolcas')
                logger.info('killing pymolcas')
                os.killpg(os.getpgid(molcas_process.pid), signal.SIGTERM)

            else:
                pass


def analyse_neci():
    import subprocess
    import tarfile

    iter = 0
    tar = tarfile.open("Iter_" + str(iter) + '.tar.gz', "r:gz")
    FCIMCstats = tar.ge

    print("Analyzing NECI output")
    logger.info("Analyzing NECI output")
    molcas_WorkDir = os.getenv('MOLCAS_WorkDir')
    plot_script = input('Enter the python plotting program')
    subprocess.Popen('python', plot_script)


if __name__ == '__main__':
    project = 'ls'
#    neci_scratch_dir = '/home/katukuri/work/Molcas/NiO/cas24in27/non-emb/NECI'
#    neci_out_file = 'out'
#    copy_to_molcas_workdir(project, neci_scratch_dir)

#    E = get_e(neci_out_file)
#    print(E)
