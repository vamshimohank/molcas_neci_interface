#. /home/katukuri/Codes/MOLCAS/molcas_config.sh
#export REMOTE_MACHINE_IP=allogin2.fkf.mpg.de
#export REMOTE_NECI_WorkDir=/algpfs/katukuri/molcas_neci
#export MOLCAS_
#export CurrDir=$PWD
export WorkDir=$PWD/tmp
. /home/katukuri/Codes/MOLCAS/molcas_mod_config.sh
pymolcas -new -f -b1 $1 &
