#!/usr/bin/env python3
from pathlib import Path
from fnmatch import fnmatch
import shutil
import csv 
import pydicom
import sys

# extract the header information from each file
def read_dicom_header(path: Path):
    # read header data - not pixel -- raise exception if doesnt exist
    try:
        return pydicom.dcmread(path, stop_before_pixels=True, force=True)
    except Exception:
        return None
    
def get_series_number(ds):
    try:
        return int(getattr(ds, "SeriesNumber", -1))
    except Exception:
        return -1

# extracting the protocol name and series description 
def get_text(ds):
    protocol = str(getattr(ds, "ProtocolName", "")).lower()
    series_desc = str(getattr(ds, "SeriesDescription", "")).lower()
    
    return f"{protocol} {series_desc}"

# classify each series to extract dwi func and anat files
def classify_series(ds) -> str:
    modality = str(getattr(ds, "Modality", "")).upper()
    
    text = get_text(ds)

    # Checking to make sure its an MR image
    if modality != "MR":
        return "ignore"
    
    # excluding derived diffusion and anat maps
    exclude_terms = [
        "adc",
        "tracew",
        "_fa",
        "colfa",
        "tensor",
        "_mpr_"
    ]
    
    # excluding any files inclduing these terms
    if any(term in text for term in exclude_terms):
        return "ignore"

    # add any patterns for dwi files as needed
    dwi_patterns = [
        "b0_ap",
        "b0_pa",
        "ep2d_diff*ref",
        "ep2d_diff*b100"
    ]

    # add any patterns for anat files as needed
    anat_patterns = [
        "t1_mp2rage",
        "t1_mprage",
        "t2_tse",
        "t2_spc",
        "flair",
        "t2_space"
    ]

    # add any patterns for func files as needed (ensure includes spinecho fmaps for ME rest runs)
    func_patterns = [
        "bold",
        "epi_cmrr",
        "fmri",
        "spinechofieldmap",
        "spin echo fieldmap"
    ]

    # label the files dwi anat or func
    if any(fnmatch(text, f"*{pattern}*") for pattern in dwi_patterns):

        # separate into fmap and func files
        if "ref" in text or "b0_pa" in text:
            return "fmap"
        
        return "dwi"

    if any(fnmatch(text, f"*{pattern}*") for pattern in anat_patterns):
        return "anat"
    
    if any(fnmatch(text, f"*{pattern}*") for pattern in func_patterns):

        if "sbref" in text:
            return "func"

        # separate into fmap and func files
        if "ref" in text or "fieldmap" in text:
            return "fmap"
        
        return "func"
    
    return "ignore"

# creating clean name without problematic characters
def clean_name(value: str) -> str:
    value = str(value).strip()

    # list of characters to remove that are not compatible with a bids conversion
    bad_chars = [" ", "/", "\\", ":", ",", "(", ")", "[", "]"]

    # replacing any of these characters with an underscore
    for char in bad_chars:
        value = value.replace(char, "_")

    return value

# creating bids compliant task names
def clean_task_name(task):
    # Removing capitals and leading/trailing white spaces
    task = str(task).strip().lower()

    # Removing underscores, dashses, and spaces
    task = task.replace("_","")
    task = task.replace("-","")
    task = task.replace(",","")
    task = task.replace(" ","")

    return task


# extracting the tasks from the input tasks
def extract_task(ds, task_list):
    text = get_text(ds)
    text_clean = clean_task_name(text)

    for task in task_list:
        task_clean = clean_task_name(task)

        if task_clean and task_clean in text_clean:
            return task_clean
    
    return ""

# getting the name for each series folder
def get_series_folder_name(ds):

    # Extracting the series number - attaching unknown if empty
    series_number = clean_name(getattr(ds, "SeriesNumber", "unknown"))

    # Extracting the protocol name - attaching unknown if empty
    description = clean_name(getattr(ds, "SeriesDescription", "unknown_protocol"))

    # returning the name of the folder for each series
    return f"series-{series_number}_{description}"

# extracting the folder name for each series (scan)
def find_dicom_series(input_root: Path):

    # seaching every file in the input path
    for folder in input_root.rglob("*"):

        # skipping if not a directory
        if not folder.is_dir():
            continue
        
        # looking for dicoms in the folder
        dicom_files = sorted(list(folder.glob("*.dcm")) + list(folder.glob("*IMA")))

        # skip if there are no dicoms in the folder
        if len(dicom_files) == 0:
            continue
        
        # extracting header information from the first dicom in the folder
        representative_dicom = dicom_files[0]
        ds = read_dicom_header(representative_dicom)

        # returning the series folder and its metadata
        if ds is not None:
            yield folder, ds

# copying each series into the dicom folder
def copy_dicom_series(
        series_path: Path, 
        ds, 
        output_root: Path, 
        subject: str, 
        session: str, 
        task_list,
        dry_run: bool = False,
):
    # extracting the category (anat, dwi, func), series, and protocol
    category = classify_series(ds)
    series_number = get_series_number(ds)
    text = get_text(ds)

    # extracting the direction
    direction = ""

    if "p>>a" in text or "p__a" in text or "p_a" in text or "p>a" in text or "pa" in text:
        direction = "PA"

    elif "a>>p" in text or "a__p" in text or "p_a" in text or "a>p" in text or "ap" in text:
        direction = "AP"

    # adding func/dwi to the extra row for fmap files
    extra = ""
    if category == "fmap":

        # for func reference maps
        if "bold" in text or "epi_cmrr" in text or "fmri" in text:
            extra = "func"

        # for spinecho fmaps
        elif "spinechofieldmap" in text or "spin echo fieldmap" in text:
            extra = "func"
        
        # for diffusion reference amps
        elif "b0" in text or "diff" in text:
            extra = "dwi"

    if category == "ignore":
        return None
    
    # extracting the task for the func files
    task = ""
    if category == "func":
        task = extract_task(ds, task_list)
    
    # asigning rest to all spin echos
    elif category == "fmap" and extra == "func":
        if "spinecho" in text or "spin echo" in text:
            task = "rest"
    
    # extracting folder name and destiantion dir 
    series_folder = get_series_folder_name(ds)

    # setting the destination dir for fmaps to dwi/func respectively
    if category == "fmap" and extra in ["func", "dwi"]:
        output_category = extra
    else:
        output_category = category 

    destination_dir = output_root / subject / session / output_category / series_folder 

    # creating destination dir and copying files
    if not dry_run:
        destination_dir.mkdir(parents=True, exist_ok=True)

        shutil.copytree(
            series_path,
            destination_dir,
            dirs_exist_ok=True
        )

    # return the data for each value
    return {
        "source": str(series_path),
        "subject": subject,
        "session": session,
        "category": category,
        "extra": extra,
        "series_folder": series_folder,
        "series_number": series_number,
        "task": task,
        "run": "",
        "dir": direction,
        "series_dir": str(destination_dir),
    }

# using the series numbers to assign the appropriate refs to the func scans
def assign_task_fmaps(rows):

    # extracting and storing the tasks and their series numbers
    func_tasks_by_series = {
        row["series_number"]: row["task"]
        for row in rows
        if row["category"] ==  "func" and row["task"]
    }

    # parsing through the fmaps 
    for row in rows:

        # skipping if not fmap file
        if row["category"] != "fmap":
            continue
        
        # skipping if not func fmap
        if row["extra"] != "func":
            continue 
        
        # making sure task row exists
        if row["task"]:
            continue

        # extracting the series number
        series_number = row["series_number"]

        # first checking for a func file with the series 1 before
        if series_number - 1 in func_tasks_by_series:
            row["task"] = func_tasks_by_series[series_number -1]

        # if that doesn't exist checking for the series 2 before
        elif series_number - 2 in func_tasks_by_series:
            row["task"] =func_tasks_by_series[series_number -2]
    
    return rows 

# assigning run number for tasks run multiple times
def assign_runs(rows):
    # initializing the row variable
    for row in rows:
        row["run"] = ""

    # count the func bold runs by task 
    bold_runs_by_task = {}

    # iterating through task runs by series number
    for row in sorted(rows, key=lambda r: r["series_number"]):

        if row["category"] != "func":
            continue 
        if get_bids_suffix(row) != "bold":
            continue

        task = row["task"] 
        if not task:
            continue 

        bold_runs_by_task[task] = bold_runs_by_task.get(task, 0) + 1
        row["run"] = bold_runs_by_task[task]

    # Looking up BOLD rows by series number
    bold_lookup = {
        row["series_number"]: row
        for row in rows
            if row["category"] == "func" 
            and get_bids_suffix(row) == "bold"
            and row["task"]
    }

    # Labeling the SBRef from nearest bold
    for row in sorted(rows, key=lambda r: r["series_number"]):
        if row["category"] != "func":
            continue

        if get_bids_suffix(row) != "sbref":
            continue

        series_number = row["series_number"]

        # Looking for the bold after the SBREF based on series number
        for offset in [1,2]:
            match = bold_lookup.get(series_number + offset)
            if match is not None:
                row["task"] = match["task"]
                row["run"] = match["run"]
                break
    
    # Matching the fmaps run number
    for row in sorted(rows, key=lambda r: r["series_number"]):
        if row["category"] != "fmap":
            continue
        if row["extra"] != "func":
            continue

        series_number = row["series_number"]

        # Checking for the task one or two series before the reference
        for offset in [-1,-2]:
            match = bold_lookup.get(series_number + offset)
            if match is not None:
                row["task"] = match["task"]
                row["run"] = match["run"]
                break
    
    return rows

# creating qc manifest to make sure the right folders were copied 
def write_manifest(rows, manifest_path: Path):

    # creating parent folder for qc csv
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    # defining the columns of the csv
    fieldnames = [
        "source",
        "subject",
        "session",
        "category",
        "task",
        "run",
        "dir",
        "series_folder",
        "series_dir",
        "series_number",
        "extra"
    ]

    # open the csv and write the rows
    with open(manifest_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

# getting the bids suffix 
def get_bids_suffix(row):
    category = row["category"]
    series_folder = row["series_folder"].lower()

    if category == "func":
        if "sbref" in series_folder:
            return "sbref"
        return "bold"
    
    if category == "dwi":
        return "dwi"
    
    if category == "fmap":
        return "epi"
    
    if category == "anat":
        if "t1" in series_folder:
            return "T1w"
        elif "dark-fluid" in series_folder or "da-fl" in series_folder or "flair" in series_folder:
            return "FLAIR"
        else:
            return "T2w"

    return ""

# creating the bids input file for the bids conversion
def write_bids_input_tsv(rows, bids_tsv_path: Path):

    bids_tsv_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "id",
        "modality",
        "suffix",
        "img",
        "[session]",
        "[task]",
        "[run]",
        "[dir]",
        "[rec]",
        "[recording]",
        "[extra]"
    ]

    with open(bids_tsv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()

        for row in rows:

            writer.writerow({
                "id": row["subject"],
                "modality": row["category"],
                "suffix": get_bids_suffix(row),
                "img": row["series_dir"],
                "[session]": row["session"],
                "[task]": row["task"],
                "[run]": row["run"],
                "[dir]": row["dir"],
                "[rec]": "",
                "[recording]": "",
                "[extra]": row["extra"],
            })

def main():
    if len(sys.argv) != 6:
    
        print(
            "Usage:\n"
            "python extract_dicoms.py "
            "/path/to/MRI_Raw "
            "/path/to/MRI_DICOM "
            "subject_id "
            "session_id "
            "task1,task2,task3... \n\n"
        )

        sys.exit(1)
    
    # defining the input arguments
    input_root = Path(sys.argv[1])

    output_root = Path(sys.argv[2])

    subject = sys.argv[3]

    session = sys.argv[4]

    task_list = sys.argv[5].split(",")

    # creating tsv paths
    manifest_path = (output_root / "manifesttsvs" / f"{subject}_{session}_manifest.tsv")
    bids_tsv_path = (output_root / "bidstsvs" / f"{subject}_{session}_bids_input.tsv")

    # for testing set to true
    dry_run = False

    rows = []

    # finding each scan and processing them
    for series_path, ds in find_dicom_series(input_root):

        row = copy_dicom_series(
            series_path=series_path,
            ds=ds,
            output_root=output_root,
            subject=subject,
            session=session,
            task_list=task_list,
            dry_run=dry_run,
        )

        # skip ignored series
        if row is not None:
            rows.append(row)
    
    # assigning tasks to fmap files
    rows = assign_task_fmaps(rows)
    rows = assign_runs(rows)

    # writing the output tsvs 
    write_manifest(rows,manifest_path)

    write_bids_input_tsv(rows,bids_tsv_path)

    # printing summary
    print(f"Relevant DICOM series found: {len(rows)}")
    print(f"Manifest TSV written to {manifest_path}")
    print(f"BIDS input TSV written to {bids_tsv_path}")
    if dry_run:
        print("Dry run only. No folders were copied. Change dry_run variable to copy")

if __name__ == "__main__":
    main()

