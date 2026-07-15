#! /bin/bash
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --account=def-jottoy
#SBATCH --job-name=fmriprep
#SBATCH --output=/home/cjacquet/scratch/SURG1F/fmriprep_logs/%x_%j.out
#SBATCH --error=/home/cjacquet/scratch/SURG1F/fmriprep_logs/%x_%j.err

# Ensure the log folder exists
mkdir -p /home/cjacquet/scratch/SURG1F/fmriprep_logs

# Navigate to and echo the directory from where you called the sbatch
cd $SLURM_SUBMIT_DIR
echo $SLURM_SUBMIT_DIR

# Load the fmriprep in a container
module load apptainer fmriprep

# Define the user inputs
SUBJ=${1}
# SES=${2}

# Define the pathway to the imporant directories
bids_dir="${SLURM_SUBMIT_DIR}/MRI_BIDS/sub-${SUBJ}"
out_dir="${SLURM_SUBMIT_DIR}/fmriprep_output"
work_dir="${SLURM_SUBMIT_DIR}/fmriprep_work"
cache_dir="${SLURM_SUBMIT_DIR}/fmriprep_cache"
log_dir="${out_dir}/fmriprep_logs"
fs_license="${out_dir}/fs_license.txt"

# Make sure each of these directories exist
mkdir -p ${out_dir} ${work_dir} ${cache_dir} ${log_dir}

# Export the apptainer enviornments 
export APPTAINERENV_TEMPLATEFLOW_HOME="/project/def-jottoy/cjacquet/templateflow"
export APPTAINER_BIND=${bids_dir},${out_dir},${log_dir},$APPTAINERENV_TEMPLATEFLOW_HOME
export APPTAINER_CACHEDIR="${cache_dir}"
export APPTAINER_TMPDIR="${cache_dir}"

# Cap the number of threads to prevent killing from OOM
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK}
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=${SLURM_CPUS_PER_TASK}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK}

# Run fmriprep
fmriprep "${bids_dir}" "${out_dir}" participant  \
    --participant-label ${SUBJ} \
    --skip-bids-validation \
    --work-dir ${work_dir} \
    --fs-license-file ${fs_license} \
    --output-spaces anat MNI152NLin6Asym:res-2 fsaverage:den-164k fsnative fsLR\
    --nprocs  ${SLURM_CPUS_PER_TASK} \
    --omp-nthreads ${SLURM_CPUS_PER_TASK} \
    --mem_mb 64000 \
    --cifti-output 91k \
#    --me-output-echos \
 #   --notrack

