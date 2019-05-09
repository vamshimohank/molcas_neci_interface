from molcas_run import *

 # please set these variables
interactive = False

neci_scratch='/algpfs/katukuri/molcas_neci/'
remote_ip='allogin2.fkf.mpg.de'
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
os.environ['MOLCAS_WorkDir'] = Molcas_WorkDir
os.environ['CurrDir']= currdir
os.environ['PYTHONWARNINGS']='ignore'


# transfer files to remote/local machine to run NECI
job_folder=str(os.getpid())
neci_work_dir=neci_scratch+job_folder+'/'

# run molcas submission script
#molcas_process = executeMolcas(molcas_submission_script,inp_file)
MOLCAS_running=True

while MOLCAS_running :
    MOLCAS_running = check_if_molcas_paused(out_file)

    # print('Transferring FciInp and FciDmp to the remote computer {0}:{1} and submitting the job'.format(remote_ip,neci_WorkDir))
    job_id=run_neci_on_remote(project)
    # print("Submiting the job to the queue ...")
    status = check_if_neci_completed(remote_ip,neci_work_dir,job_id)

    if status :
        get_rdms_from_neci(neci_work_dir)
        if interactive :
            try:
                input("Continue with MOLCAS run? press any key")
            except SyntaxError:
                pass
    activate_molcas()

