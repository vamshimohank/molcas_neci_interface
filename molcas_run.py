import sys
import subprocess
#import sh

#molcas_exe='/home/katukuri/bin/pymolcas'
molcas_exe='/home/katukuri/bin/molcas'
fciqmc_exe='srun /home/katukuri/software/FIDIS/NECI_STABLE/build_new/bin/neci'

project=sys.argv[1]
in_file = sys.argv[1]+'.inp'
out_file = sys.argv[1]+'.out'

def exec_neci(project):
	subprocess.call("cp %s.FciDmp FCIDUMP" % project,shell=True)
	fciqmc_infile=project+'.FciInp'
	fciqmc_outfile=project+'.FciOut'

	subprocess.call("%s  %s > %s" % (fciqmc_exe, fciqmc_infile, fciqmc_outfile), shell=True)

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
#		molcas_process=subprocess.Popen("%s  %s -o %s -b 1" % (molcas_exe,in_file,out_file),shell=True,close_fds=True)
		molcas_process=subprocess.Popen("%s  %s -f %s -b 1" % (molcas_exe,in_file,out_file),shell=True,close_fds=True)
	except subprocess.CalledProcessError as err:
		raise err
	return molcas_process

# RUN Molcas
molcas_process=executeMolcas(in_file,out_file)
if molcas_process.poll() == None:
	print("Running MOLCAS")

while molcas_process.poll() == None:
	check_molcas_status(out_file)
	exec_neci(project)
#	e=float(subprocess.check_output("grep 'Final energy' %s |awk '{print $7}'" % out_file,shell=True))
	e=float(subprocess.check_output("grep 'Final energy' %s |awk '{print $7}'" % out_file,shell=True))
	print(e)
	subprocess.call("echo %f > NEWCYCLE" % e, shell=True)
	time.sleep(20)
	subprocess.call("rm NEWCYCLE",shell=True)

#ras_macro_iter=int(subprocess.check_output("grep 'Maximum number of macro iterations' %s|awk '{print $6}'" % out_file,shell=True))

	# check if molcas has reached the 1st iteration
#if macro_iter < max_macro_iter:
#	neci=check_molcas_status(out_file)

	#Run NECI
#if neci=='yes':
#	exec_neci(project)
#else:
#	print('convergence reached')
