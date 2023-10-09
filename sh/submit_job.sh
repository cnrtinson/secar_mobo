#!/bin/bash -login

### define resources needed:
### walltime - how long you expect the job to run
#SBATCH --time=6-23:00:00
#SBATCH --begin=now

### nodes:ppn - how many nodes & cores per node (ppn) that you require
#SBATCH --ntasks=10
#SBATCH --nodes=1
### --constraint="lac"
###SBATCH --account="ptg"

### mem: amount of memory that the job will need
#SBATCH --mem-per-cpu=5G
### you can give your job a name for easier identification
#SBATCH -J pygmo_optimize
#SBATCH --array=1

### error/output file specifications
#SBATCH -o /mnt/simulations/secarml/secar_mobo_tinson/sh/slurmfiles/moead_gen_4f_%a.txt
#SBATCH -e /mnt/simulations/secarml/secar_mobo_tinson/sh/slurmfiles/moead_gen_4f_%a.txt
### load necessary modules, e.g.
###SBATCH --mail-user=herman67@msu.edu
###SBATCH --mail-type=FAIL
###module restore gpflow
conda activate secar_moead_custom
cd /mnt/simulations/secarml/secar_mobo_tinson/py
./optimize.py 10${SLURM_ARRAY_TASK_ID} 0
scontrol show job ${SLURM_JOB_ID}

