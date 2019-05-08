import sys,os,shutil
import subprocess
import time
#import sh


def get_e(out_file):
	f = open(out_file)
	Pr = False
	string='REDUCED DENSITY MATRICES'
	for line in f.readlines():
	        if string in line:
	                E=line.split()[8]
	                return E
	                break
	f.close()

def copy_to_molcas_workdir(project,neci_scratch_dir):
        cmd="scp allogin2.fkf.mpg.de:" + neci_scratch_dir + '/TwoRDM* ./tmp/'
        subprocess.call("%s" % cmd,shell=True)
        cmd="scp allogin2.fkf.mpg.de:" + neci_scratch_dir + '/out .'
        subprocess.call("%s" % cmd,shell=True)
#        shutil.move('./tmp/TwoRDM_aaaa.1', './tmp/'+project+'.TwoRDM_aaaa')
#        shutil.move('./tmp/TwoRDM_abab.1', './tmp/'+project+'.TwoRDM_abab')
#        shutil.move('./tmp/TwoRDM_abba.1', './tmp/'+project+'.TwoRDM_abba')
#        shutil.move('./tmp/TwoRDM_bbbb.1', './tmp/'+project+'.TwoRDM_bbbb')
#        shutil.move('./tmp/TwoRDM_baba.1', './tmp/'+project+'.TwoRDM_baba')
#        shutil.move('./tmp/TwoRDM_baab.1', './tmp/'+project+'.TwoRDM_baab')

def copy_to_main_dir(project,neci_scratch_dir):
	shutil.copyfile(os.path.join(neci_scratch_dir,'TwoRDM_abab.1'), './'+project+'.TwoRDM_abab')
	shutil.copyfile(os.path.join(neci_scratch_dir,'TwoRDM_abba.1'), './'+project+'.TwoRDM_abba')
	shutil.copyfile(os.path.join(neci_scratch_dir,'OneRDM.1'), './'+project+'.OneRDM')

def transfer_neci_files_to_remote(remote_ip,user,remote_folder_absolute_path):
	from fabric import Connection
    c=Connection(remote_ip)
	c.run('mkdir {0}'.format(remote_folder_absolute_path))


def exec_neci(project,molcas_WorkDir,neci_scratch_dir='tmp'):
	import os
	remote_machine="allogin2.fkf.mpg.de"
	user='katukuri'
	neci_WorkDir="/algpfs/katukuri/molcas_neci/"+str(os.getpid())
	tmp_neci_dir='tmp_neci_dir'
	# if  os.path.isdir(tmp_neci_dir) :
	# 	os.removedirs(tmp_neci_dir)
	# 	os.mkdir(tmp_neci_dir)
	# shutil.copyfile(os.path.join(molcas_WorkDir, project+'.FciDmp'), tmp_neci_dir+'/FCIDUMP')
	# shutil.copyfile(os.path.join(molcas_WorkDir, project+'.FciInp'), tmp_neci_dir+'/input')

	transfer_neci_files_to_remote(remote_machine,user,neci_WorkDir)
	cmd = 'scp -r '+ tmp_neci_dir + remote_machine + neci_WorkDir
	subprocess.call("%s" % cmd,shell=True)
	# shutil.copyfile(project+'.FciInp', os.path.join(neci_scratch_dir,project+'.FciInp'))
	# fciqmc_infile=os.path.join(neci_scratch_dir,project+'.FciInp')
	# fciqmc_outfile=os.path.join(neci_scratch_dir,project+'.FciOut')

#	outfiletmp = os.path.join(neci_scratch_dir,project+'.FciOut')
#	files = os.listdir(neci_scratch_dir + '.')
#	# Search for an unused output file.
#	i = 1
#	while outfiletmp in files:
#		outfiletmp = fciqmcci.outputFileRoot + '_' + str(i)
#		i += 1
##    logger.info(fciqmcci, 'FCIQMC output file: %s', outfiletmp)
#	fciqmcci.outputFileCurrent = outfiletmp
#	fciqmc_outfile = os.path.join(fciqmcci.scratchDirectory, outfiletmp)

	# RUN NECI
	"""
	os.chdir(neci_scratch_dir)
	subprocess.call("%s  %s > %s" % (fciqmc_exe, project+'.FciInp',project+'.FciOut'), shell=True)
	os.chdir('../')
	E=get_e(fciqmc_outfile)
	copy_to_main_dir(project,neci_scratch_dir)
	return E
	"""

def check_molcas_status(out_file):
	import time
	time.sleep(20)
	while 1:
		line=str(subprocess.check_output("tail -1 %s" % out_file,shell=True))
#		print(line)
		if ("your_RDM_Energy" in line):
			print("Perfoming CASSCI with NECI") 
			break
#        return neci

def executeMolcas(submission_script,project):
	try:
		#molcas_process=subprocess.Popen("%s  %s -o %s -b 1" % (molcas_exe,in_file,out_file),shell=True,close_fds=True)
		cmd="sh " + submission_script + " "
		# molcas_process=subprocess.Popen("%s  %s -o " % (cmd,project),stdout=subprocess.PIPE)
		molcas_process=subprocess.Popen("%s  %s -o " % (cmd,project),shell=True,close_fds=True) #,stdout=subprocess.PIPE)
		# molcas_process=subprocess.Popen("%s  %s -f %s -b 1" % (molcas_exe,in_file,out_file),shell=True,close_fds=True)
	except subprocess.CalledProcessError as err:
		raise err
	return molcas_process

def check_if_molcas_done(out_file):
	f = open(out_file, 'r')
	time.sleep(5)
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
				# print('MOLCAS ', line)
				f.close()
				return molcas_WorkDir
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
