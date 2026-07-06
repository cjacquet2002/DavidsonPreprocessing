# Davidson Preprocessing Pipeline

A preprocessing pipeline for converting MRI DICOM data into BIDS format.

## Features

- Automatic DICOM series extraction
- BIDS conversion
- Multi-echo BOLD support
- SBRef handling
- Spin echo fieldmap support
- Automatic run assignment
- AP/PA fieldmap generation
- Automatic IntendedFor generation
- JSON sanitization

## Requirements

- Python 3.10+
- dcm2niix
- FSL
- Compute Canada or Linux environment

## Notes
- Multi-echo resting states must be called "rest"
- All multiecho spinechos will be assigned to the resting state scans

## Installation

```bash
git clone https://github.com/cjacquet2002/DavidsonPreprocessing.git
cd DavidsonPreprocessing
bash setup.sh
```

## Running

```bash
sbatch BIDS_Conversion.sh input.tsv
```
