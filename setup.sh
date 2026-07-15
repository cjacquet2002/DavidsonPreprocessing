#! /bin/bash

# load necessary modules
module load StdEnv/2023 scipy-stack/2026a fsl nibabel/5.2.0 dcm2niix

# Change to path to repo if located elsewhere
cd /home/cjacquet/scratch/SURG1F/Preprocessing_pipeline
pip install -e . 
