from molcas_neci_interface.molcas_neci_interface import *

import argparse
import os, signal
 # Command-line arguments
from molcas_neci_interface.molcas_neci_interface import get_rdms_from_neci

parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=42,width=120))
parser.add_argument('-i', '--interactive', help='Interactive run: you have to provide input if the molcas needs to be continued', action='store_true')
parser.add_argument('filename', help='script to run molcas locally', nargs='?', metavar='input_file | script')
parser.usage = '{0} [options] [input_file | script ...]'.format(parser.prog)

args = vars(parser.parse_args())

if (not args['filename']):
    # parser.description = 'MOLCAS has been found at {0}'.format(Molcas.molcas)
    parser.print_help()
    # return(0)
    exit()


 # please set these variables
interactive = args['interactive']
if interactive:
    print('Running interactively')
    # exit()

remote_ip='allogin2.fkf.mpg.de'
neci_scratch='/algpfs/katukuri/molcas_neci/'
neci_job_script='neci_submit.job'
Molcas_WorkDir=os.getcwd()+'/tmp/'
currdir = os.getcwd()

project='o2'
molcas_submission_script = 'run_molcas.sh' # a bash script on local PC

# molcas project details
inp_file=project+'.inp'
out_file = project+'.log'

# set environment variables
os.environ['REMOTE_MACHINE_IP'] = remote_ip
os.environ['REMOTE_NECI_WorkDir'] = neci_scratch
os.environ['NECI_JOB_SCRIPT'] = neci_job_script
os.environ['WorkDir'] = Molcas_WorkDir
os.environ['MOLCAS_WorkDir'] = Molcas_WorkDir
os.environ['CurrDir']= currdir
os.environ['PYTHONWARNINGS']='ignore'


# transfer files to remote/local machine to run NECI
job_folder=str(os.getpid())
neci_work_dir=neci_scratch+job_folder+'/'


# run molcas submission script
molcas_process = executeMolcas(inp_file)
MOLCAS_running=True

iter = 0
while MOLCAS_running :
    MOLCAS_running = check_if_molcas_paused(out_file)

    job_id=run_neci_on_remote(project)
    status = check_if_neci_completed(remote_ip,neci_work_dir,job_id)
    if status :
        get_rdms_from_neci(iter,job_folder)
        if interactive :
            try:
                inp_val = input("Continue with MOLCAS run? y/N \n ")
                if inp_val.split()[0] == 'N' or inp_val.split()[0] == 'n':
                    inp_molcas_run = input("(a) Abort MOLCAS ?  \n"
                                           "(b) Analyse NECI OUTPUT \n")
                    if inp_molcas_run.split()[0] == 'a' :
                        os.killpg(os.getpgid(molcas_process.pid), signal.SIGTERM)
                        molcas_process.kill()
                        exit()
                    elif inp_molcas_run.split()[0] == 'b':
                        analyse_neci()
                elif inp_val.split()[0] == 'Y' or inp_val.split()[0] == 'y':
                    activate_molcas()
            except SyntaxError:
                pass
        else:
            activate_molcas()
            iter += 1

