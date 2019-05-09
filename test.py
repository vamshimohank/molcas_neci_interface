from molcas_neci_interface.molcas_neci_interface import executeMolcas, check_if_molcas_done, exec_neci

project = 'o2'
inp_file=project+'.inp'
out_file = project+'.log'
sub_script = 'run_molcas.sh'


#subprocess.call("%s" % cmd,shell=True)

molcas_process = executeMolcas(sub_script,inp_file)
molcas_WorkDir=check_if_molcas_done(out_file)
print(molcas_WorkDir)
exec_neci(project,molcas_WorkDir)

# output = molcas_process.stdout.read()
# output_lines = output.split(b'\n')
# print(output_lines)
#print(molcas_process)