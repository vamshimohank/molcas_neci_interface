from molcas_run import *

 # please set these variables

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


# run molcas submission script
molcas_process = executeMolcas(molcas_submission_script,inp_file)
molcas_WorkDir=check_if_molcas_done(out_file)

# transfer files to remote/local machine to run NECI
job_folder=str(os.getpid())
neci_work_dir=neci_scratch+job_folder+'/'

job_id=run_neci_on_remote(project)
check_if_job_running(remote_ip,job_id)
check_if_neci_is_done(neci_work_dir)

# check_if_neci_is_done(neci_WorkDir)
# get_rdms_from_neci(neci_WorkDir)