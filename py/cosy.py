#!/mnt/misc/sw/x86_64/all/anaconda/python3.7/bin/python

# make sure above path points to the version of python where you have pygmo installed 
# nscl servers
#!/mnt/misc/sw/x86_64/all/anaconda/python3.7/bin/python
# hpcc servers
#!/mnt/home/herman67/anaconda3/envs/pygmo/bin/python


#import commands
import sys, math
import os, shutil
import subprocess as commands
import re
from numpy.random import random as rng
from numpy import array, append, zeros, power, isnan
import timeit

magnet_names = array(["Q1", "Q2", "B1", "B2", "HEX1", "Q3", "Q4", "Q5", "B3", "B4", "HEX2", "Q6", "Q7", "HEX3", "OCT1", "Q8", "Q9", "B5", "B6", "Q10", "Q11", "Q12", "Q13", "B7", "B8", "Q14", "Q15", "UMCP", "Viewer"])
# define the dimensions of the magnet chambers
magnet_dims = array([[90,80],[140,102],[240,60],[240,60],[240,142],[220,142],[146,126],[102,102],[156,104],[156,104],[240,102],[280,110],[280,110],[165,115],[102,102],[100,100],[120,90],[148,66],[148,66],[180,96],[240,91],[140,140],[100,100],[130,60],[130,60],[100,100],[100,100],[75/1.41,75/1.41],[70,70]])

# define the nominal values for the objective function
fNom = array([245.5333762546184, 256.5533534865096, 1.016965710603861, 0.0497233197451071])
fNom = array([0.02285401532682956, 0.04181594290692345, 3.422466427009127, 0.27344973981231574, 0.05])
fNom = array([0.04191152312524359, 0.03457401051019327, 0.08790627203524701, 6.199553823734411, 0.4920320554679182])
fNom = array([0.0009201399656821892, 0.0007943037376589886, 0.0008652899891146716, 3.422466427009127, 0.27344973981231574])
# define the nominal qvalue array (array is sent to cosy as a power of 2, i.e. 0 => 2^0 = 1 * nominal value)
qNom = zeros(19)+1

# define a non nominal qvalue array, if checking the values
qNew = array([0.5924182514791451,-0.8758860089293923,-0.6100796679131815,-0.14615536797341183,0.9770480402400011,-0.7391592447117457,-0.7498637465288235,0.16544225901836773,0.19998299730932922,-0.6100283855003581,-0.25827968836883713,-1.5,1.5,1.9,-1.9])
qNew = power(2,qNew)
qNew = array([2.93038477,1.90063726,0.426385,  0.43573147,0.8350062,  0.26068104,
 0.61171371,2.05445898,0.3762753, 3.31110943,3.97101987,3.91936971,
 0.80816148,2.69208215,0.62319133])
qNew = array([-0.020059, 0.533494,-0.985974,-0.549243,-0.645459,-0.863731,-0.358719,-0.456463,-0.793326, 0.615835, 0.269274,-0.451374,-0.903452, -0.05333,-0.798368, 0.706399,-0.588547, 0.098331, 0.964641])

# set working DIR for PYGMO, FOX, COSY
PYGMO_DIR = '../'
FOX_DIR = PYGMO_DIR + 'fox/'
#hpcc servers
#COSY_DIR = '/mnt/home/herman67/cosy/COSY10.0/'
#nscl servers
COSY_DIR = PYGMO_DIR + 'COSY10.0/'

# write the qvalue array to a fox file for cosy to run
def write_fox(qs=qNom, name=None, directory=FOX_DIR, fox_file='SEC_neutrons_WF_14m_v1.fox'):
    # how many magnets to set
    input_len = len(qs)
    # if less than qNom, use qNom values (0) for remainder
    if (len(qNom)-input_len>0):
        for i in range(len(qNom)-input_len):
            qs = append(qs,qNom[i+input_len])
    # get rand number for the temporary file
    if name==None:
        rand = rng()
    else:
        rand = name
    # get the fox file for the simulation and change the qvalues
    cosy_input = FOX_DIR + fox_file
    text = None
    with open(cosy_input, 'r') as f:
        text = f.readlines()

    start_line = 0 
    # find where in the file to change
    for i in range(len(text)):
        # dummy text line in the fox file that the code searches for to find the qvalue setting
        if "SET MAGNETS" in text[i]:
            start_line = i+1
#            print(text[i], text[start_line])
    # change the q setttings
    magnet_i = 0
    for i in range(len(qs)):
        magnet_i += 1
        if i < 15:
            text[i+start_line] = "Q{0}_SC:= {1};\n".format(magnet_i,qs[i])
        elif i < 18: 
            magnet_i = i - 14
            text[i+start_line] = "H{0}_SC:= {1};\n".format(magnet_i,qs[i])
        else: 
            magnet_i = 1
            text[i+start_line] = "O{0}_SC:= {1};\n".format(magnet_i,qs[i])
    # temporary output file
    cosyFilename = directory + 'pygmoCosy'+str(rand)+'.fox'
    # if by some ridiculous chance we pick the same number as another iteration, find new number
    while os.path.exists(cosyFilename):
        rand = rng()
        cosyFilename = directory + 'pygmoCosy'+str(rand)+'.fox'
    lisFilename = directory + 'pygmoCosy'+str(rand)+'.lis'
    # write out the fox file
    with open(cosyFilename, 'w') as f:
        f.writelines(text)
    # return filenames for cosy to find
    return cosyFilename, lisFilename


# Function that runs cosy 
# check problem.py and optimize.py for more on how the operation works
# idea is that evolve() in optimize.py will call fitness() in problem.py
#   fitness() will pass a set of magnet factors (between 0.5 and 2.0) to cosyrun
#   and will return the resulting objectives to the algorithm
def cosyrun(qs=qNom):

    # make fox file and get name
    cosyFilename, lisFilename = write_fox(qs,fox_file="SEC_neutrons_WF_off_v1.fox")
    cosyFilename2, lisFilename2 = write_fox(qs,fox_file="SEC_neutrons_WF_off_DE_rays_v1.fox")
    
    #Run cmd
    cmd = COSY_DIR + 'cosy'
    # timer for diagnostics
    startTime = timeit.default_timer()
    # run cosy 
    output = commands.run([cmd ,cosyFilename], capture_output=True)
    # print time
    print ('Running time (sec): %f' % (timeit.default_timer() - startTime))

    # timer for diagnostics
    startTime = timeit.default_timer()
    # run cosy2 
    output2 = commands.run([cmd ,cosyFilename2], capture_output=True)
    # print time
    print ('Running time (sec): %f' % (timeit.default_timer() - startTime))

    # get output and now convert into the necessary values to return to pygmo
    stripped = output.stdout.strip().decode('utf8','strict')
    split = stripped.split()
    print(split)
    # get output and now convert into the necessary values to return to pygmo
    stripped2 = output2.stdout.strip().decode('utf8','strict')
    split2 = stripped2.split()
    print(split2)

    # initiate all variables to be read, and bools for the reader to check
    xdim, ydim = [], []
    fp1res, fp1espread, fp1xdim = 0, 0, 0
    fp2res, fp2espread, fp2xdim = 0, 0, 0
    fp3res, fp3espread, fp3xdim = 0, 0, 0
    beamspotsize = 0
    xdim_bool, ydim_bool = False, False
    fp1res_bool, fp1espread_bool, fp1xdim_bool = False, False, False
    fp2res_bool, fp2espread_bool, fp2xdim_bool = False, False, False
    fp3res_bool, fp3espread_bool, fp3xdim_bool = False, False, False
    beamspotsize_bool = False

    # my method could probably be better optimized but this works and is mostly straight-forward
    #   idea is just that keywords are output for each variable, e.g. "Xdim" for the Xdim for a magnet dimension
    #   the below code will check if the bool is true and if so write the corresponding value and false the bool
    #   in total we parse through all the cosy output and find all the different variables
    for i in range(len(split)):
        if xdim_bool:
            xdim.append(float(split[i]))
            xdim_bool = False
        if ydim_bool:
            ydim.append(float(split[i]))
            ydim_bool = False
        if fp1xdim_bool:
            fp1xdim = (float(split[i])*1000)
            fp1xdim_bool = False
        if fp2xdim_bool:
            fp2xdim = (float(split[i])*1000)
            fp2xdim_bool = False
        if fp3xdim_bool:
            fp3xdim = (float(split[i])*1000)
            fp3xdim_bool = False
        if beamspotsize_bool:
            beamspotsize = power(float(split[i]),0.5)
            beamspotsize_bool = False
        if split[i].strip() == "Xdim":
            xdim_bool = True
        if split[i].strip() == "Ydim":
            ydim_bool = True
        if split[i].strip() == "FP1Xdim":
            fp1xdim_bool = True
        if split[i].strip() == "FP2Xdim":
            fp2xdim_bool = True
        if split[i].strip() == "FP3Xdim":
            fp3xdim_bool = True
        if split[i].strip() == "BeamSpotSize":
            beamspotsize_bool = True
    for i in range(len(split2)):
        if fp2res_bool:
            fp2res = (float(split2[i]))
            fp2res_bool = False
        if fp3res_bool:
            fp3res = (float(split2[i]))
            fp3res_bool = False
        if fp1res_bool:
            fp1res = (float(split2[i]))
            fp1res_bool = False
        if split2[i].strip() == "FP1DE":
            fp1res_bool = True
        if split2[i].strip() == "FP2DE":
            fp2res_bool = True
        if split2[i].strip() == "FP3DE":
            fp3res_bool = True

    # scale factor to account for the beam spot issue
    #   even the nominal setting is outside the bounds...
    scale = 1e9 
    max_width = 0
    # setup value to be returned, here 4 different objectives
    objs = 5
    resol = zeros(objs) 
    print(qs)
    for i in range(len(magnet_dims)):
        # if no x-ydim values, just return outside constraints (all 1e9)
        if len(xdim) < len(magnet_dims) or len(ydim) < len(magnet_dims):
            resol = zeros(objs)+1e9         
            break            
        if fp1xdim == 0 or fp2xdim == 0 or fp3xdim == 0 or isnan(fp1xdim) or isnan(fp2xdim) or isnan(fp3xdim):
            resol = zeros(objs)+1e9         
            break            
        # find xbound, ybound
        xbound = (abs(xdim[i])*1000)
        ybound = (abs(ydim[i])*1000)
        # if ratio of *bound to magnet_dim is larger than max_width, set max_width
        max_width = max(xbound/magnet_dims[i][0],ybound/magnet_dims[i][1],max_width)
#        print(i, magnet_names[i], "{:.2f}".format(xbound), magnet_dims[i][0], "{:.2f}".format(ybound), magnet_dims[i][1])
        # if *bound more than 4x magnet_dim, or is nan, return outside constraints
        if xbound > magnet_dims[i][0] * scale or ybound > magnet_dims[i][1] * scale or isnan(xbound) or isnan(ybound):
#            print("{:.2f}".format(xbound), magnet_dims[i][0], "{:.2f}".format(ybound), magnet_dims[i][1])
            resol = zeros(objs)+1e9         
            break
        # if within constraints, set resol temporarily
        resol = [fp1res/fp1xdim,fp2res/fp2xdim,fp3res/fp3xdim,max_width,beamspotsize]
    print(resol)
    # if within constraints, set resol as a ratio to nominal
    if max(resol) < 1e9:
        for i in range(len(resol)):
            # make sure we are working with positive numbers
            if resol[i] > 0: 
                resol[i] = float(resol[i])
            else:
                if i in [0,1,2]:
                    resol[i] = float(1e-9)
                else:
                    resol[i] = float(1e9)
            # we try to maximize fp*res, but the algorithm wants to minimize
            #   objective values, so we have to take an inverse ratio
            #   i.e. a ratio < 1.0 is good
            if i in [0,1,2]:
                resol[i] = fNom[i]/resol[i]
            # we want to minimize max_width and beamspotsize, so just take resol/fNom
            else:    
                resol[i] = resol[i]/fNom[i]
    print(resol)            

    # remove old cosy fox and lis file
    commands.run(['rm','-f',cosyFilename])
    commands.run(['rm','-f',lisFilename])
    commands.run(['rm','-f',cosyFilename2])
    commands.run(['rm','-f',lisFilename2])

    # return the objective values
    return (resol)
    

if __name__ == "__main__":
    # if running from console, just run the nominal setting
    print(cosyrun(qNom))
    # if running from console, just run the assigned setting
    print(cosyrun(qNew))


