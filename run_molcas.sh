#. /home/katukuri/Codes/MOLCAS/molcas_config.sh
. /home/katukuri/Codes/MOLCAS/molcas_mod_config.sh
currdir=$PWD
export WorkDir=$currdir/tmp
pymolcas -new -f -b1 $1 &
