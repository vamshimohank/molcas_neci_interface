#!/usr/bin/env python


def read_input_json():
    json_inpfile = sys.argv[1]
    with open(json_inpfile) as json_file:
        inp = json.load(json_file)
    return inp


def set_variables():
    import os

    os.environ['PYTHONWARNINGS'] = 'ignore'

    inp = read_input_json()

    if inp['molcas']['interactive'] == 'True':
        interactive = True
        print('Running interactively')
        logger.info('Running interactively')
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
            logger.info("skip_iter_0 is True")
            os.environ['skip_iter_0'] = inp['compute_node']['skip_iter_0']
        else:
            os.environ['skip_iter_0'] = "False"
    else:
        # print("skip_iter_0 is False")
        os.environ['skip_iter_0'] = "False"

    # set environment variables
    job_folder = str(os.getpid()) + '/'
    os.environ['project'] = project
    os.environ['REMOTE_MACHINE_IP'] = inp['compute_node']['remote_ip']
    os.environ['REMOTE_NECI_WorkDir'] = os.path.join(inp['compute_node']['neci_scratch'] , job_folder)
    os.environ['NECI_JOB_SCRIPT'] = inp['compute_node']['neci_job_script']
    os.environ['WorkDir'] = inp['molcas']['molcas_workdir']
    os.environ['MOLCAS_WorkDir'] = inp['molcas']['molcas_workdir']
    os.environ['CurrDir'] = os.getcwd()
    os.environ['USER'] = inp['compute_node']['user']
    if 'password' in inp['compute_node']:
        os.environ['PASSWORD'] = inp['compute_node']['password']
    os.environ['scheduler'] = inp['compute_node']['scheduler']
    os.environ['neci_exec_time'] = str(inp['compute_node']['neci_exec_time'])

    # Write the info into log

    logger.info('Remote computer for NECI calculations : {0}'.format(os.getenv('REMOTE_MACHINE_IP')))
    logger.info('Working directory on the remote computer : {0}'.format(os.getenv('REMOTE_NECI_WorkDir')))

    return inp_file, out_file, interactive


def interactive_run_neci(project, it):
    neci_work_dir = os.getenv('REMOTE_NECI_WorkDir')

    if os.getenv('skip_iter_0') == "True" and it == 0:
        input("Skipping the 0th iteration, "
              "make sure to copy existing RDMs to molcas work dir to finish the first iteration, "
              "enter any key after that \n")
        status = True
        # os.environ['skip_iter_0'] = False
    else:
        while True:
            run_molcas = input('Continue to run NECI on {0} (y/n)\n'
                               .format(os.getenv('REMOTE_MACHINE_IP')))
            if run_molcas.lower() == 'y' or run_molcas.lower() == 'n':
                break
            else:
                print("Wrong choice! Try again\n")
                logger.info("Wrong choice! Try again\n")

        if run_molcas.split()[0] == 'Y' or run_molcas.split()[0] == 'y':
            job_id = run_neci_on_remote(project, it)
            input('Enter any key when NECI is done\n')
            status = check_if_neci_completed(neci_work_dir, job_id, interactive)
        elif run_molcas.split()[0] == 'N' or run_molcas.split()[0] == 'n':
            inp_molcas_run = input("(a) Abort MOLCAS ?  \n"
                                   "(b) Change remote node for NECI calculation \n"
                                   "(c) more options to come \n")
            if inp_molcas_run.split()[0] == 'a':
                os.killpg(os.getpgid(molcas_process.pid), signal.SIGTERM)
                exit()
            elif inp_molcas_run.split()[0] == 'b':
                print("this option is yet to be implemented !")
                logger.info("this option is yet to be implemented !")
                print("Aborting MOLCAS for now !!")
                logger.info("Aborting MOLCAS for now !!")
                os.killpg(os.getpgid(molcas_process.pid), signal.SIGTERM)
                exit()

    return status


def interactive_activate_molcas():
    while True:
        inp_val = input("Continue with MOLCAS run? y/N \n ")
        if inp_val.lower() == 'y' or inp_val.lower() == 'n':
            break
        else:
            print("Wrong choice! Try again\n")
            logger.info("Wrong choice! Try again\n")

    if inp_val.split()[0].lower() == 'n':
        while True:
            inp_molcas_run = input("(a) Abort MOLCAS ?  \n"
                                   "(b) Analyse NECI OUTPUT \n")
            if inp_molcas_run.lower() == 'a' or inp_val.lower() == 'b':
                break
            else:
                print("Wrong choice! Try again\n")
                logger.info("Wrong choice! Try again\n")

        if inp_molcas_run.split()[0].lower() == 'a':
            os.killpg(os.getpgid(molcas_process.pid), signal.SIGTERM)
            # molcas_process.kill()
            exit()
        elif inp_molcas_run.split()[0].lower() == 'b':
            analyse_neci()
    elif inp_val.split()[0].lower() == 'y':
        activate_molcas()


def wait_time(t):
    # from tqdm import tqdm
    # for i in tqdm(range(t)):
    #     time.sleep(i)
    import time

    from progress.bar import Bar  # sudo pip install progress

    bar = Bar('Processing', max=20, suffix='%(index)d/%(max)d - %(percent).1f%% - %(eta)ds')
    for i in range(20):
        time.sleep(2)  # Do some work
        bar.next()
    bar.finish()
    return None


def run_neci(interactive, it):
    import os

    # creat a dedicated folder for neci run in the scratch
    neci_work_dir = os.getenv('REMOTE_NECI_WorkDir')
    project = os.getenv('project')
    # while MOLCAS_running:
    try:
        if interactive:
            status = interactive_run_neci(project, neci_work_dir, it)
        else:
            # special case if the first NECI iteration is to be skipped
            if os.getenv('skip_iter_0') == "True" and it == 0:
                input("copy existing RDMs and neci.out to molcas work dir, "
                      "enter any key after that \n")
                status = True
                # os.environ['skip_iter_0'] = False
            else:
                job_id = run_neci_on_remote(project, it)
                #print('Waiting for an estimated {0} seconds for NECI run'
                #      .format(float(os.getenv('neci_exec_time'))))
                #logger.info('Waiting for an estimated {0} seconds for NECI run'
                #      .format(float(os.getenv('neci_exec_time'))))
                # wait_time(int(os.getenv('neci_exec_time')))
                #time.sleep(float(os.getenv('neci_exec_time')))
                status = check_if_neci_completed(neci_work_dir, job_id, interactive)
        return status
    except KeyboardInterrupt:
        os.killpg(os.getpgid(molcas_process.pid), signal.SIGTERM)


def restart_rasscf(status, it):
    try:
        if status:
            if os.getenv('skip_iter_0') == "True" and it == 0:
                pass
            else:
                get_rdms_from_neci(it)

            if interactive:
                try:
                    interactive_activate_molcas()
                except SyntaxError:
                    pass
            else:
                activate_molcas()
    except KeyboardInterrupt:
        os.killpg(os.getpgid(molcas_process.pid), signal.SIGTERM)

    # return MOLCAS_running




if __name__ == '__main__':

    from molcas_neci_interface import *
    import time, os, signal, sys, json
    print('----- MOLCAS NECI INTERFACE ----')
    logger.info('MOLCAS NECI Interface ')
    logger.info('May 2018: Vamshi M Katukuri ')

    try:
        # set all the variables
        inp_file, out_file, interactive = set_variables()

        # Run pymolcas
        molcas_process = executeMolcas(inp_file)


        MOLCAS_running = True
        print('pymolcas running with id {}'.format(os.getpgid(molcas_process.pid)))
        logger.info('pymolcas running with id {}'.format(os.getpgid(molcas_process.pid)))
        read_interrupt_inp()

        it = 0
        while MOLCAS_running:
            print('----- Iteration {} ------'.format(it))
            logger.info('----- Iteration {} ------'.format(it))
            MOLCAS_running = check_if_molcas_paused(out_file)
            read_interrupt_inp()
            status = run_neci(interactive, it)
            read_interrupt_inp()
            restart_rasscf(status, it)
            read_interrupt_inp()
            it = it + 1

    except KeyboardInterrupt:
        print('\n killing molcas subprocess')
        logger.info('\n killing molcas subprocess')
        os.killpg(os.getpgid(molcas_process.pid), signal.SIGTERM)
        # print('Sending llcancel command to the remote machine')
        MOLCAS_running = False
        time.sleep(3)
        # molcas_process.kill()
        exit()
    # except Exception as e:
    #     print(e)
    #     print("killing pymolcas")
    #     os.killpg(os.getpgid(molcas_process.pid), signal.SIGTERM)
    #     exit()
