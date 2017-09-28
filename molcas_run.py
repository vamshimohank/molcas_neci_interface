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

def copy_to_main_dir(project,neci_scratch_dir):
	shutil.copyfile(os.path.join(neci_scratch_dir,'TwoRDM_aaaa.1'), './'+project+'.TwoRDM_aaaa')
	shutil.copyfile(os.path.join(neci_scratch_dir,'TwoRDM_abab.1'), './'+project+'.TwoRDM_abab')
	shutil.copyfile(os.path.join(neci_scratch_dir,'TwoRDM_abba.1'), './'+project+'.TwoRDM_abba')
	shutil.copyfile(os.path.join(neci_scratch_dir,'OneRDM.1'), './'+project+'.OneRDM')

def exec_neci(neci_scratch_dir,project):
	shutil.copyfile(project+'.FciDmp', neci_scratch_dir+'/FCIDUMP')
	shutil.copyfile(project+'.FciInp', os.path.join(neci_scratch_dir,project+'.FciInp'))
	fciqmc_infile=os.path.join(neci_scratch_dir,project+'.FciInp')
	fciqmc_outfile=os.path.join(neci_scratch_dir,project+'.FciOut')

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
	os.chdir(neci_scratch_dir)
	subprocess.call("%s  %s > %s" % (fciqmc_exe, project+'.FciInp',project+'.FciOut'), shell=True)
	os.chdir('../')
	E=get_e(fciqmc_outfile)
	copy_to_main_dir(project,neci_scratch_dir)
	return E


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

def executeMolcas(in_file,out_file):
	try:
		molcas_process=subprocess.Popen("%s  %s -o %s -b 1" % (molcas_exe,in_file,out_file),shell=True,close_fds=True)
#		molcas_process=subprocess.Popen("%s  %s -f %s -b 1" % (molcas_exe,in_file,out_file),shell=True,close_fds=True)
	except subprocess.CalledProcessError as err:
		raise err
	return molcas_process



if __name__ == '__main__':

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
