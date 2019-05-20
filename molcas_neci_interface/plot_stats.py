
import os
import numpy as np

os.environ['MOLCAS_WorkDir']=os.getcwd()+'/tmp/'
file_stats=molcas_WorkDir=os.getenv('MOLCAS_WorkDir')+'FCIMCStats'

dat = np.loadtxt(file_stats,dtype=float,comments='#')

it                 = dat[:, 0]
Shift              = dat[:, 1]
WalkerCng          = dat[:, 2]
GrowRate           = dat[:, 3]
TotWalkers         = dat[:, 4]
Annihil            = dat[:, 5]
NoDied             = dat[:, 6]
NoBorn             = dat[:, 7]
ProjE              = dat[:, 8]
AvShift            = dat[:, 9]
AvShift            = dat[:,10]
ProjEThisCyc       = dat[:,11]
NoatHF             = dat[:,12]
NoatDoubs          = dat[:,13]
AccRat             = dat[:,14]
UniqueDets         = dat[:,15] 
IterTime           = dat[:,16]
FracSpawnFromSing  = dat[:,17]
WalkersDiffProc    = dat[:,18] 
TotImagTime        = dat[:,19]
ProjEThisIter      = dat[:,20]
HFInstShift        = dat[:,21]
TotInstShift       = dat[:,22]
Tot-Proj.E.ThisCyc = dat[:,23]
HFContribtoE       = dat[:,24]
NumContribtoE      = dat[:,25]
HF_weight          = dat[:,26]
mod_Psi            = dat[:,27]
Inst_S2            = dat[:,28]
Inst_S2_           = dat[:,29]
AbsProjE           = dat[:,30]
PartsDiffProc      = dat[:,31]
mod_Semistoch_by_mod_Psi = dat[:,32]
MaxCycSpawn        = dat[:,33]


