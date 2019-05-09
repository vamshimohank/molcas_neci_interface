import sys,os,shutil
import subprocess
import time
#import sh

import sys

os.environ['PYTHONWARNINGS']="ignore"

if not sys.warnoptions:
    import os, warnings
    warnings.simplefilter("default") # Change the filter in this process
    os.environ["PYTHONWARNINGS"] = "ignore"

def if_file_exists_in_remote(remote_ip,file_name_with_full_path):
	from fabric import Connection
	from patchwork.files import exists
	# remote_ip=os.getenv('REMOTE_MACHINE_IP')
	user=os.getenv('USER')
	c=Connection(remote_ip,user=user)
	if exists(c,file_name_with_full_path):
		return True
	else:
		return False

def activate_molcas():
	molcas_WorkDir=os.getenv('MOLCAS_WorkDir')
	f = open(molcas_WorkDir+'neci.out')
	string='REDUCED DENSITY MATRICES'
	for line in f.readlines():
		if string in line:
			E=line.split()[8]
			print(E)
			# return E
			break
	f.close()
	f = open(molcas_WorkDir+"NEWCYCLE","w+")
	f.write(E)
	f.close()

def copy_to_molcas_workdir(project,neci_scratch_dir):
	cmd="scp allogin2.fkf.mpg.de:" + neci_scratch_dir + '/TwoRDM* ./tmp/'
	subprocess.call("%s" % cmd,shell=True)
	cmd="scp allogin2.fkf.mpg.de:" + neci_scratch_dir + '/out .'
	subprocess.call("%s" % cmd,shell=True)

def copy_to_main_dir(project,neci_scratch_dir):
	shutil.copyfile(os.path.join(neci_scratch_dir,'TwoRDM_abab.1'), './'+project+'.TwoRDM_abab')
	shutil.copyfile(os.path.join(neci_scratch_dir,'TwoRDM_abba.1'), './'+project+'.TwoRDM_abba')
	shutil.copyfile(os.path.join(neci_scratch_dir,'OneRDM.1'), './'+project+'.OneRDM')

def run_neci_on_remote(project):

	from fabric import Connection

	import sys

	import os

	if not sys.warnoptions:
		import os, warnings
		warnings.simplefilter("ignore") # Change the filter in this process
		os.environ["PYTHONWARNINGS"] = "default"

	remote_ip=os.getenv('REMOTE_MACHINE_IP')
	remote_WorkDir=os.getenv('REMOTE_NECI_WorkDir')
	molcas_WorkDir=os.getenv('MOLCAS_WorkDir')
	CurrDir=os.getenv('CurrDir')
	user=os.getenv('USER')
	neci_job_script=os.getenv('NECI_JOB_SCRIPT')
	job_folder=str(os.getpid())
	neci_WorkDir=remote_WorkDir+'/'+job_folder+'/'

	c=Connection(remote_ip,user=user)
	print('Transferring FciInp and FciDmp to the remote computer {0}:{1}'.format(remote_ip,neci_WorkDir))
	if not if_file_exists_in_remote(remote_ip,neci_WorkDir):
		c.run('mkdir {0}'.format(neci_WorkDir))
	c.put(molcas_WorkDir+'/'+project+'.FciInp',remote=neci_WorkDir)
	c.put(molcas_WorkDir+'/'+project+'.FciDmp',remote=neci_WorkDir)
	c.put(CurrDir+'/'+neci_job_script,remote=neci_WorkDir)
	print("Submiting the job to the queue ...")
	with c.cd(neci_WorkDir):
		job_submit_line=c.run('llsubmit {0}'.format(neci_job_script))
	job_id=job_submit_line.stdout.split()[3]
	# sys.stdout.write(job_submit_line)
	c.close()
	return job_id

	# return neci_WorkDir


def check_if_neci_completed(remote_ip,neci_work_dir,job_id):
	from time import sleep
	from datetime import datetime
	from fabric import Connection
	c=Connection(remote_ip)
	result=c.run('llq -j {0}'.format(job_id))
	status=result.stdout.split()[19]
	while status != "R":
		if status == "I":
			print('Job waiting in queue')
		if status == "I":
			print('Job waiting in queue')
		sleep(10)
		result=c.run('llq -j {0}'.format(job_id))
		status=result.stdout.split()[19]
	print('Job running ....')
	print('checking if RDMs are created ....')
	file_name_with_full_path=neci_work_dir+'TwoRDM_aaaa.1'
	while if_file_exists_in_remote(remote_ip,file_name_with_full_path) == False :
		sleep(10)
		print('NECI is still running: {0}'.format(datetime.now()))
	if if_file_exists_in_remote(remote_ip,file_name_with_full_path):
		print('NECI is done, Send the RDMs to activate MOLCAS run?')
		try:
			input("Press enter to continue")
			return True
		except SyntaxError:
			pass
           
	return True


def get_rdms_from_neci(neci_WorkDir):
	from fabric import Connection
	remote_ip=os.getenv('REMOTE_MACHINE_IP')
	user=os.getenv('USER')
	c=Connection(remote_ip,user=user)

	molcas_WorkDir=os.getenv('MOLCAS_WorkDir')
#	remote_WorkDir=os.getenv('REMOTE_NECI_WorkDir')
	# neci_WorkDir=remote_WorkDir+job_folder+'/'
	print('Copying RDMs and NECI output from')
	print(neci_WorkDir)
	print(' to ')
	print(molcas_WorkDir)
	c.get(neci_WorkDir+'TwoRDM_aaaa.1',local=molcas_WorkDir+'TwoRDM_aaaa.1') #,local=molcas_WorkDir)
	c.get(neci_WorkDir+'TwoRDM_abab.1',local=molcas_WorkDir+'TwoRDM_abab.1')
	c.get(neci_WorkDir+'TwoRDM_abba.1',local=molcas_WorkDir+'TwoRDM_abba.1')
	c.get(neci_WorkDir+'TwoRDM_bbbb.1',local=molcas_WorkDir+'TwoRDM_bbbb.1')
	c.get(neci_WorkDir+'TwoRDM_baba.1',local=molcas_WorkDir+'TwoRDM_baba.1')
	c.get(neci_WorkDir+'TwoRDM_baab.1',local=molcas_WorkDir+'TwoRDM_baab.1')
	c.get(neci_WorkDir+'out',local=molcas_WorkDir+'neci.out')
	c.close()
	# iter=0
	with c.cd(neci_WorkDir):
		# iter_folder='Iter_'+str(iter)
		# c.run('mkdir {0}'.format(iter_folder))
		# c.run('mv TwoRDM* {0}'.format(iter_folder))
		# c.run('mv out {0}/neci.out'.format(iter_folder))
		# c.run('mv out neci.out'.format(iter_folder))
		c.run('rm TwoRDM*')
		# iter += 1
	try:
		input("Continue with MOLCAS run? press any key")
		c.close()
	except SyntaxError:
		c.close()
		pass


"""
def activate_molcas():

	import time
	time.sleep(20)

	molcas_WorkDir=os.getenv('MOLCAS_WorkDir')
	out_file='neci.out'
	E=get_e(molcas_WorkDir,out_file)
"""


"""
	while 1:
		line=str(subprocess.check_output("tail -1 %s" % out_file,shell=True))
#		print(line)
		if ("your_RDM_Energy" in line):
			print("Perfoming CASSCI with NECI")
			break
#        return neci
"""

def executeMolcas(submission_script,project):
	try:
		#molcas_process=subprocess.Popen("%s  %s -o %s -b 1" % (molcas_exe,in_file,out_file),shell=True,close_fds=True)
		cmd="sh " + submission_script + " "
		# molcas_process=subprocess.Popen("%s  %s -o " % (cmd,project),stdout=subprocess.PIPE)
		molcas_process=subprocess.Popen("%s  %s -o " % (cmd,project),shell=True,close_fds=True) #,stdout=subprocess.PIPE)
		print('MOLCAS running ...')
		# molcas_process=subprocess.Popen("%s  %s -f %s -b 1" % (molcas_exe,in_file,out_file),shell=True,close_fds=True)
	except subprocess.CalledProcessError as err:
		raise err
	return molcas_process

def check_if_molcas_paused(out_file):
	time.sleep(20)
	f = open(out_file, 'r')
	line_temp=''
	while True:

		line = f.readline()
		if not line :
			time.sleep(2)
			print('Nothing New')
		else:
			# print(line.split())
			if len(line.split()) != 0 and line.split()[0] == "PAUSED":
				molcas_WorkDir=line_temp.split()[0]
				print('Files for NECI are produced', )
				f.close()
				return True
			else:
				line_temp=line


if __name__ == '__main__':
     
        project = 'ls' 
        neci_scratch_dir='/home/katukuri/work/Molcas/NiO/cas24in27/non-emb/NECI'
        neci_out_file = 'out'
        copy_to_molcas_workdir(project,neci_scratch_dir)

        E = get_e(neci_out_file)
        print(E)
        """
	cmd="export WorkDir=./"
	subprocess.call("%s" % cmd,shell=True)

	neci_scratch_dir="./NECI"
	if not os.path.exists(neci_scratch_dir):
		os.makedirs(neci_scratch_dir)

	molcas_exe='/home/katukuri/bin/pymolcas'

#molcas_exe='/home/katukuri/bin/molcas'
#fciqmc_exe='srun /home/katukuri/software/FIDIS/NECI_STABLE/build_new/bin/neci'
#fciqmc_exe='srun /home/katukuri/software/FIDIS/NECI_STABLE/build_deprecated/bin/neci'
	fciqmc_exe='srun /home/katukuri/software/DENEB/NECI_STABLE/build/bin/neci'

#project=sys.argv[1]
	project='hs_neci'
	in_file = project+'.inp'
	out_file = project+'.out'
# RUN Molcas
	molcas_process=executeMolcas(in_file,out_file)
	if molcas_process.poll() == None:
		print("Running MOLCAS")

	while molcas_process.poll() == None:
		check_molcas_status(out_file)
		E=exec_neci(neci_scratch_dir,project)
		print('NECI RDM Energy=%s' % E)
		subprocess.call("echo %s > NEWCYCLE" % E, shell=True)
#		print('copying files for molcas to read')
#		subprocess.call("mv TwoRDM_aaaa.1 %s.TwoRDM_aaaa" % project, shell=True)
#		subprocess.call("mv TwoRDM_abab.1 %s.TwoRDM_abab" % project, shell=True)
#		subprocess.call("mv TwoRDM_abba.1 %s.TwoRDM_abba" % project, shell=True)
#		subprocess.call("mv OneRDM.1 %s.OneRDM" % project, shell=True)
#		subprocess.call("echo %s > NEWCYCLE" % E, shell=True)
#		time.sleep(1)
#		print('deleating NEWCYCLE')
#		subprocess.call("rm NEWCYCLE",shell=True)

#ras_macro_iter=int(subprocess.check_output("grep 'Maximum number of macro iterations' %s|awk '{print $6}'" % out_file,shell=True))

	# check if molcas has reached the 1st iteration
#if macro_iter < max_macro_iter:
#	neci=check_molcas_status(out_file)

	#Run NECI
#if neci=='yes':
#	exec_neci(project)
#else:
#	print('convergence reached')
        """
