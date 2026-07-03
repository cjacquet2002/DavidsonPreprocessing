#!/bin/bash 
#SBATCH --account=def-jottoy
#SBATCH --job-name=bidsconversion
#SBATCH --array=2
#SBATCH --cpus-per-task=4
#SBATCH --time=01:00:00
#SBATCH --mem=16G
#SBATCH --output=/home/cjacquet/scratch/logs/%x_%A_%a.out
#SBATCH --error=/home/cjacquet/scratch/logs/%x_%A_%a.err

# load necessary modules
module load StdEnv/2023 scipy-stack/2026a fsl nibabel/5.2.0

dicom_dir=/home/cjacquet/scratch/SURG1F/MRI_DICOM
bids_dir=/home/cjacquet/scratch/SURG1F/MRI_BIDS

input_file=${1}

line=$(sed -n "$((SLURM_ARRAY_TASK_ID+1))p" "$input_file")
IFS=$'\t' read subject session raw_dir tasks <<< "$line"

echo $subject $session $raw_dir $tasks
# Give path to metajson
meta_json=/home/cjacquet/scratch/SURG1F/Preprocessing_pipeline/study_meta_data_example.json

# Running the python script to separate the dicoms and write the input tsv
# Change the path to the python script if necessary

extract-dicoms \
    $raw_dir \
    $dicom_dir \
    $subject \
    $session \
    $tasks

input_tsv=${dicom_dir}/bidstsvs/${subject}_${session}_bids_input.tsv
echo $input_tsv

davidson-convert \
    --input_file $input_tsv \
    --meta_json $meta_json \
    --project $subject \
    --output $bids_dir