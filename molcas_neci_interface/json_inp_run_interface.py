#!/usr/bin/env python
from molcas_neci_interface import *


def set_variables():
    import time, os, signal, sys, json

    os.environ['PYTHONWARNINGS'] = 'ignore'

    json_inpfile = sys.argv[1]
    # print(json_inpfile)

    with open(json_inpfile) as json_file:
        inp = json.load(json_file)

    if inp['molcas']['interactive'] == 'True':
        interactive = True
        print('Running interactively')
    else:
        interactive = False

    # molcas project details
    project = inp['molcas']['project']
    inp_file = project + '.inp'
    out_file = project + '.log'

    # special case if you want to skip the first NECI calculation
    if 'skip_iter_0' in inp['compute_node']:
        if inp['compute_node']['skip_iter_0'] == "True":
            print("skip_iter_0 is True")
            os.environ['skip_iter_0'] = inp['compute_node']['skip_iter_0']
        else:
            os.environ['skip_iter_0'] = "False"
    else:
        # print("skip_iter_0 is False")
        os.environ['skip_iter_0'] = "False"

    # set environment variables
    os.environ['project'] = project
    os.environ['REMOTE_MACHINE_IP'] = inp['compute_node']['remote_ip']
    os.environ['REMOTE_NECI_WorkDir'] = inp['compute_node']['neci_scratch']
    os.environ['NECI_JOB_SCRIPT'] = inp['compute_node']['neci_job_script']
    os.environ['WorkDir'] = inp['molcas']['molcas_workdir']
    os.environ['MOLCAS_WorkDir'] = inp['molcas']['molcas_workdir']
    os.environ['CurrDir'] = os.getcwd()
    os.environ['USER'] = inp['compute_node']['user']
    # os.environ['PASSWORD']            = inp['compute_node']['password']
    os.environ['scheduler'] = inp['compute_node']['scheduler']

    # transfer files to remote/local machine to run NECI

    return inp_file, out_file, interactive


def run_neci(MOLCAS_running, interactive, out_file):
    import os

    # creat a dedicated folder for neci run in the scratch
    job_folder = str(os.getpid())
    neci_work_dir = os.getenv('REMOTE_NECI_WorkDir') + job_folder + '/'
    project = os.getenv('project')
    it = 0
    while MOLCAS_running:
        try:
            MOLCAS_running = check_if_molcas_paused(out_file)

            if interactive:
                if os.getenv('skip_iter_0') == "True" and it == 0:
                    input("Skipping the 0th iteration, "
                          "make sure to copy existing RDMs to molcas work dir to finish the first iteration, "
                          "enter any key after that \n")
                    status = True
                    # os.environ['skip_iter_0'] = False
                else:
                    run_molcas = input('Continue to run NECI on {0} (y/n)\n'
                                       .format(os.getenv('REMOTE_MACHINE_IP')))
                    if run_molcas.split()[0] == 'Y' or run_molcas.split()[0] == 'y':
                        job_id = run_neci_on_remote(project, it)
                        status = check_if_neci_completed(neci_work_dir, job_id)
                    elif run_molcas.split()[0] == 'N' or run_molcas.split()[0] == 'n':
                        inp_molcas_run = input("(a) Abort MOLCAS ?  \n"
                                               "(b) Change remote node for NECI calculation \n"
                                               "(c) more options to come \n")
                        if inp_molcas_run.split()[0] == 'a':
                            os.killpg(os.getpgid(molcas_process.pid), signal.SIGTERM)
                            exit()
                        elif inp_molcas_run.split()[0] == 'b':
                            print("this option is yet to be implemented !")
                            print("Aborting MOLCAS for now !!")
                            os.killpg(os.getpgid(molcas_process.pid), signal.SIGTERM)
                            exit()
                    # reread_inp()

            else:
                if os.getenv('skip_iter_0') == "True" and it == 0:
                    input("copy existing RDMs and neci.out to molcas work dir, "
                          "enter any key after that \n")
                    status = True
                    # os.environ['skip_iter_0'] = False
                else:
                    job_id = run_neci_on_remote(project, it)
                    status = check_if_neci_completed(neci_work_dir, job_id)
            if status:

                if os.getenv('skip_iter_0') == "True" and it == 0:
                    pass
                else:
                    get_rdms_from_neci(it, job_folder)

                if interactive:
                    try:
                        inp_val = input("Continue with MOLCAS run? y/N \n "
                                        "(Please dont press anything else, it might crash :()")
                        # check_yes_or_no(inp_val)
                        if inp_val.split()[0] == 'N' or inp_val.split()[0] == 'n':
                            inp_molcas_run = input("(a) Abort MOLCAS ?  \n"
                                                   "(b) Analyse NECI OUTPUT \n"
                                                   "(Please dont press anything else, it might crash :()")
                            if inp_molcas_run.split()[0] == 'a':
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
                it = it + 1
        except KeyboardInterrupt:
            os.killpg(os.getpgid(molcas_process.pid), signal.SIGTERM)


if __name__ == '__main__':

    from molcas_neci_interface import *
    import time, os, signal, sys, json

    # set all the variables
    inp_file, out_file, interactive = set_variables()
    # run molcas submission script
    molcas_process = executeMolcas(inp_file)
    MOLCAS_running = True
    try:
        run_neci(MOLCAS_running, interactive, out_file)
    except KeyboardInterrupt:
        print('\n killing molcas subprocess')
        os.killpg(os.getpgid(molcas_process.pid), signal.SIGTERM)
        # print('Sending llcancel command to the remote machine')
        MOLCAS_running = False
        time.sleep(3)
        # molcas_process.kill()
        exit()
    except Exception as e:
        print(e)
        print("killing pymolcas")
        os.killpg(os.getpgid(molcas_process.pid), signal.SIGTERM)
        exit()
