#!/usr/bin/env python

def set_variables():
    from molcas_neci_interface.molcas_neci_interface import *
    import time, os, signal, sys, json

    os.environ['PYTHONWARNINGS']      = 'ignore'

    json_inpfile = sys.argv[1]
    print(json_inpfile)

    with open(json_inpfile) as json_file:
        inp = json.load(json_file)

    interactive = inp['molcas']['interactive']
    if interactive:
        print('Running interactively')

# molcas project details
    project  = inp['molcas']['project']
    inp_file = project+'.inp'
    out_file = project+'.log'

# set environment variables
    os.environ['REMOTE_MACHINE_IP']   = inp['compute_node']['remote_ip']
    os.environ['REMOTE_NECI_WorkDir'] = inp['compute_node']['neci_scratch']
    os.environ['NECI_JOB_SCRIPT']     = inp['compute_node']['neci_job_script']
    os.environ['WorkDir']             = inp['molcas']['molcas_workdir']
    os.environ['MOLCAS_WorkDir']      = inp['molcas']['molcas_workdir']
    os.environ['CurrDir']             = os.getcwd() 
    os.environ['USER']                = inp['compute_node']['user']
#os.environ['PASSWORD']            = inp['compute_node']['password']
    os.environ['scheduler']           = inp['compute_node']['scheduler']


# transfer files to remote/local machine to run NECI

# creat a dedicated folder for neci run in the scratch 
    job_folder    = str(os.getpid())
    neci_work_dir = inp['compute_node']['neci_scratch'] + job_folder + '/'

        
def start_script(MOLCAS_running):
    it = 0
    while MOLCAS_running :
        try :
            MOLCAS_running = check_if_molcas_paused(out_file)

            if interactive :
                run_molcas = ('MOLCAS PAUSED, Continue to run NECI on {0}'.format(inp['compute_node']))
                if run_molcas.split()[0] == 'Y' or run_molcas.split()[0] == 'y':
                    job_id=run_neci_on_remote(project,it)
                    status = check_if_neci_completed(neci_work_dir,job_id)
                elif run_molcas.split()[0] == 'N' or run_molcas.split()[0] == 'n':
                    if run_molcas.split()[0] == 'N' or run_molcas.split()[0] == 'n':
                        inp_molcas_run = input("(a) Abort MOLCAS ?  \n"
                                           "(b) more option to come \n")
                        if inp_molcas_run.split()[0] == 'a' :
                            os.killpg(os.getpgid(molcas_process.pid), signal.SIGTERM)
                            exit()
                else:
                    reread_inp()

            else :
                job_id=run_neci_on_remote(project,it)
                status = check_if_neci_completed(neci_work_dir,job_id)
            if status :
                get_rdms_from_neci(it,job_folder)
                if interactive :
                    try:
                        inp_val = input("Continue with MOLCAS run? y/N \n ")
                        if inp_val.split()[0] == 'N' or inp_val.split()[0] == 'n':
                            inp_molcas_run = input("(a) Abort MOLCAS ?  \n"
                                               "(b) Analyse NECI OUTPUT \n")
                            if inp_molcas_run.split()[0] == 'a' :
                                os.killpg(os.getpgid(molcas_process.pid), signal.SIGTERM)
                            # molcas_process.kill()
                                exit()
                            elif inp_molcas_run.split()[0] == 'b':
                                analyse_neci()
                        elif inp_val.split()[0] == 'Y' or inp_val.split()[0] == 'y':
                            activate_molcas()
                    except SyntaxError:
                        pass
                else:
                    activate_molcas()
                it += 1

if __name__ == '__main__':
    from molcas_neci_interface.molcas_neci_interface import *
    import time, os, signal, sys, json

    # set all the variables
    set_variables():
    # run molcas submission script
    molcas_process = executeMolcas(inp_file)
    MOLCAS_running=True
    try :
        start_script(MOLCAS_running)
    except KeyboardInterrupt :
        print('\n killing molcas subprocess')
        os.killpg(os.getpgid(molcas_process.pid), signal.SIGTERM)
    # print('Sending llcancel command to the remote machine')
        MOLCAS_running=False
        time.sleep(3)
    #molcas_process.kill()
        exit()
    except Exception as e:
        print("killing pymolcas")
        os.killpg(os.getpgid(molcas_process.pid), signal.SIGTERM)
        exit()
