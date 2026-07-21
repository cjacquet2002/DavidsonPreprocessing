# requirement
import csv
import json
import os
import pathlib
import sys
import shutil
import subprocess
import pandas as pd
import numpy as np
import nibabel as nib



# Classes
# generic img class
class img2bids:

    def __init__(self, id:str, mod:str, sufx:str):
        self.id = f'sub-{id}'
        self.mod = mod
        self.sufx = sufx

        return



    def setup(self, bids_dir:str, ses = None):
        self.bids_dir = bids_dir
        self.ses = ses
        if "mask" in self.sufx:
            self.subj_bids_dir = os.path.join(bids_dir, "derivatives", "brain_mask", self.id, f"ses-{ses}", self.mod if ses else os.path.join(bids_dir, "derivatives", "brain_mask", self.id, self.mod))
        else:
            self.subj_bids_dir = os.path.join(bids_dir, self.id, f"ses-{ses}", self.mod if ses else os.path.join(bids_dir, self.id, self.mod))
        os.makedirs(self.subj_bids_dir, exist_ok = True)
        self.subj_bids_img = f'{self.id}_ses-{ses}' if ses else f'{self.id}'
        self.subj_bids_img_fmap_for = self.subj_bids_img




    def convert(self, img, meta_json, dcm_lvl = 0, **kwargs):
        self.img = img
        self.task_var = None
        self.fieldmap_mod = None
        self.fieldmap_mod_dir = None
        self.subj_bids_img_anci = None
        
        # loading the json data into variables
        with open(meta_json, 'r') as jfile:
            self.proj_json = json.load(jfile)

        try:
            # PET conversion
            if self.mod == 'pet':
                if 'pet' in self.sufx.lower():
                    # task
                    if 'task' in kwargs and kwargs.get('task') is not None:
                        self.task_var = kwargs.get('task')
                        self.subj_bids_img += f'_task-{self.task_var}'

                    
                    # tracer
                    if 'ancil' in kwargs and kwargs.get('ancil') is not None:
                        self.tracer = kwargs.get('ancil')
                        if self.tracer in self.proj_json['modalities']['pet']['tracers']:
                            # tracer
                            self.subj_bids_img += f'_trc-{self.tracer}'


                    # recon
                    if 'rec' in kwargs and kwargs.get('rec') is not None:
                        self.rec_var = kwargs.get('rec')
                        self.subj_bids_img += f'_rec-{self.rec_var}'


                    # runs
                    run = kwargs.get("run")

                    if run not in (None, ""):
                        self.run_var = run
                        self.subj_bids_img += f'_run-{self.run_var}'


                    # output extension suffix
                    self.subj_bids_img += f'_{self.sufx}'


            # anat conversion
            if self.mod == 'anat':
                if self.sufx in ["T1w", "T2w", "FLAIR"]:
                    # acq param
                    if self.proj_json['modalities']['anat']['acq'] is not None:
                        self.acq_var = self.proj_json['modalities']['anat']['acq']
                        self.subj_bids_img += f'_acq-{self.acq_var}'


                    # contrast 
                    if self.proj_json['modalities']['anat']['ce'] is not None:
                        self.ce_var = self.proj_json['modalities']['anat']['ce']
                        self.subj_bids_img += f'_ce-{self.ce_var}'


                    # recon
                    if 'rec' in kwargs and kwargs.get('rec') is not None:
                        self.rec_var = kwargs.get('rec')
                        self.subj_bids_img += f'_rec-{self.rec_var}'


                    # runs
                    run = kwargs.get("run")

                    if run not in (None, ""):
                        self.run_var = run
                        self.subj_bids_img += f'_run-{self.run_var}'


                    # part
                    if self.proj_json['modalities']['anat']['part'] is not None:
                        self.part_var = self.proj_json['modalities']['anat']['part']
                        self.subj_bids_img += f'_part-{self.part_var}'


                    # output extension suffix
                    if 'mask' in self.sufx.lower():
                        self.subj_bids_img += f'_desc-{self.sufx}'

                    else:
                        self.subj_bids_img += f'_{self.sufx}'


            # func conversion
            if self.mod == 'func':
                if self.sufx.lower() in ["bold", "sbref"]:
                    # task
                    if 'task' in kwargs and kwargs.get('task') is not None:
                        self.task_var = kwargs.get('task')
                        self.subj_bids_img += f'_task-{self.task_var}'


                    # acq param
                    if self.proj_json['modalities']['func']['acq'] is not None:
                        self.acq_var = self.proj_json['modalities']['func']['acq']
                        self.subj_bids_img += f'_acq-{self.acq_var}'


                    # contrast
                    if self.proj_json['modalities']['func']['ce'] is not None:
                        self.ce_var = self.proj_json['modalities']['func']['ce']
                        self.subj_bids_img += f'_ce-{self.ce_var}'


                    # recon
                    if 'rec' in kwargs and kwargs.get('rec') is not None:
                        self.rec_var = kwargs.get('rec')
                        self.subj_bids_img += f'_rec-{self.rec_var}'


                    # direction
                    if self.proj_json['modalities']['func']['dir'] is not None:
                        self.dir_var = self.proj_json['modalities']['func']['dir']
                        self.subj_bids_img += f'_dir-{self.dir_var}'


                    # runs
                    run = kwargs.get("run")

                    if run not in (None, ""):
                        self.run_var = run
                        self.subj_bids_img += f'_run-{self.run_var}'


                    # echo
                    if self.proj_json['modalities']['func']['echo'] is not None:
                        self.part_var = self.proj_json['modalities']['func']['echo']
                        self.subj_bids_img += f'_echo-{self.part_var}'


                    # part
                    if self.proj_json['modalities']['func']['part'] is not None:
                        self.part_var = self.proj_json['modalities']['func']['part']
                        self.subj_bids_img += f'_part-{self.part_var}'


                    # output extension suffix
                    self.subj_bids_img += f'_{self.sufx}'


            # dwi conversion
            if self.mod == 'dwi':
                if "dwi" in self.sufx.lower():
                    # acq param
                    if self.proj_json['modalities']['dwi']['acq'] is not None:
                        self.acq_var = self.proj_json['modalities']['dwi']['acq']
                        self.subj_bids_img += f'_acq-{self.acq_var}'


                    # recon
                    if 'rec' in kwargs and kwargs.get('rec') is not None:
                        self.rec_var = kwargs.get('rec')
                        self.subj_bids_img += f'_rec-{self.rec_var}'


                    # direction
                    if self.proj_json['modalities']['dwi']['dir'] is not None:
                        self.dir_var = self.proj_json['modalities']['dwi']['dir']
                        self.subj_bids_img += f'_dir-{self.dir_var}'


                    # runs
                    run = kwargs.get("run")

                    if run not in (None, ""):
                        self.run_var = run
                        self.subj_bids_img += f'_run-{self.run_var}'


                    # part
                    if self.proj_json['modalities']['dwi']['part'] is not None:
                        self.part_var = self.proj_json['modalities']['dwi']['part']
                        self.subj_bids_img += f'_part-{self.part_var}'


                    # output extension suffix
                    self.subj_bids_img += f'_{self.sufx}'


            # fieldmap b0 conversion
            if self.mod == 'fmap':
                ## fieldmap ref data
                if 'ancil' in kwargs and kwargs.get('ancil') is not None:
                    self.fieldmap_mod = kwargs.get('ancil')
                    self.fieldmap_mod_dir = os.path.join(f"ses-{self.ses}", self.fieldmap_mod) if self.ses else os.path.join(self.fieldmap_mod)

                    if self.fieldmap_mod in self.proj_json['modalities']['fmap']['intendedfor']:
                        self.subj_bids_img_anci = self.subj_bids_img_fmap_for

                        # sufx related to fieldmap
                        if self.fieldmap_mod == "dwi":
                            self.fieldmap_sufx = "dwi"
                        elif self.fieldmap_mod == "func":
                            self.fieldmap_sufx = "bold"

                        # task
                        if self.fieldmap_mod == "func":
                            if 'task' in kwargs or kwargs.get('task') is not None:
                                self.task_var = kwargs.get('task')
                                self.subj_bids_img_anci += f'_task-{self.task_var}'

                        # acq param
                        if self.proj_json['modalities'][self.fieldmap_mod]['acq'] is not None:
                            self.acq_var = self.proj_json['modalities'][self.fieldmap_mod]['acq']
                            self.subj_bids_img_anci += f'_acq-{self.acq_var}'


                        # recon
                        if 'rec' in kwargs and kwargs.get('rec') is not None:
                            self.rec_var = kwargs.get('rec')
                            self.subj_bids_img_anci += f'_rec-{self.rec_var}'

                        # runs
                        run = kwargs.get("run")

                        if run not in (None, ""):
                            self.run_var = run
                            self.subj_bids_img_anci += f'_run-{self.run_var}'

                        # part
                        if self.proj_json['modalities'][self.fieldmap_mod]['part'] is not None:
                            self.part_var = self.proj_json['modalities'][self.fieldmap_mod]['part']
                            self.subj_bids_img_anci += f'_part-{self.part_var}'

                        # output extension suffix
                        self.subj_bids_img_anci += f'_{self.fieldmap_sufx}'

                # acq label
                if self.fieldmap_mod == "dwi":
                    self.subj_bids_img += "_acq-dwi"

                elif self.fieldmap_mod == "func":
                    if 'task' in kwargs and kwargs.get('task') is not None:
                        self.task_var = kwargs.get('task')
                        self.subj_bids_img += f"_acq-{self.task_var}"
                    else: 
                        self.subj_bids_img += "_acq-rest"

                # recon
                if 'rec' in kwargs and kwargs.get('rec') is not None:
                    self.rec_var = kwargs.get('rec')
                    self.subj_bids_img += f'_rec-{self.rec_var}'

                # runs
                run = kwargs.get("run")

                if run not in (None, ""):
                    self.run_var = run
                    self.subj_bids_img += f'_run-{self.run_var}'

                # direction
                dir_var = kwargs.get("dir")

                if dir_var in (None, ""):
                    raise ValueError(
                        f"Fieldmap '{os.path.basename(self.img)}' is missing a direction (AP/PA)." 
                        "Please populate the [dir] column in the BIDS input TSV.")
                
                self.dir_var = dir_var
                self.subj_bids_img += f"_dir-{self.dir_var}"

                # part
                if self.proj_json['modalities']['fmap'][self.fieldmap_mod]['part'] is not None:
                    self.part_var = self.proj_json['modalities']['fmap'][self.fieldmap_mod]['part']
                    self.subj_bids_img += f'_part-{self.part_var}'

                # output extension suffix
                self.subj_bids_img += f'_{self.sufx}'



        except Exception as e:
            if self.mod == 'pet':
                print("Sorry, something went wrong your pet run.")
                print(e)

            elif self.mod == 'anat':
                print("Sorry, something went wrong your T1w run.")
                print(e)

            elif self.mod == 'func':
                print("Sorry, something went wrong your func run.")
                print(e)
            
            elif self.mod == 'dwi':
                print("Sorry, something went wrong your dwi run.")
                print(e)

            elif self.mod == 'fmap':
                print("Sorry, something went wrong your fmap run.")
                print(e)


        # save the bids outputs                
        self.bids_format = in_out(self.img, self.mod, self.sufx, self.proj_json, self.subj_bids_dir, self.subj_bids_img, dcm_lvl)        
        self.bids_format.save(intendedfor_dir = self.fieldmap_mod_dir, 
                              intendedfor = self.subj_bids_img_anci,
                              **kwargs
                              )




# input and output class
class in_out:

    def __init__(self, in_img, mod, sufx, study_json, output_dir, output, dcm_lvl = 0):        
        self.in_img = in_img
        self.mod = mod
        self.sufx = sufx
        self.study_json = study_json
        self.output_dir = output_dir
        self.output = output
        self.out = f'{output_dir}/{output}'
        self.dcm_lvl = dcm_lvl      

        return


    def save(self, **kwargs):
        self.dcm_lvl_res = kwargs.get('dcm_lvl_df') if 'dcm_lvl_df' in kwargs and kwargs.get('dcm_lvl_df') is not None else None

        if not os.path.exists(f'{self.out}.nii.gz'):
            # nii inputs
            if os.path.exists(self.in_img) and os.path.isfile(self.in_img) and os.path.basename(self.in_img).split('.')[-1] == 'nii':
                
                # img save
                mod_save('nii', self.mod, self.sufx, self.in_img, self.out)

                # save related files
                mod_related_files_save(self.mod, self.study_json, self.in_img, self.out, 
                                       **kwargs
                                       )
            

            # nii.gz inputs
            elif os.path.exists(self.in_img) and os.path.isfile(self.in_img) and os.path.basename(self.in_img).split('.', maxsplit = 1)[-1] == 'nii.gz':
                
                # img save
                mod_save('nii.gz', self.mod, self.sufx, self.in_img, self.out)


                # save related files
                mod_related_files_save(self.mod, self.study_json, self.in_img, self.out, 
                                       **kwargs
                                       )


            # dcm inputs
            elif os.path.exists(self.in_img) and os.path.isdir(self.in_img):
                if self.dcm_lvl == 0:
                    # img save
                    mod_save('dcm', self.mod, self.sufx, self.in_img, self.out)

                    # save related files
                    mod_related_files_save(self.mod, self.study_json, self.in_img, self.out, 
                                           **kwargs
                                           )


                else:
                    # img save
                    mod_save('dcm', self.mod, self.sufx, self.in_img, self.out, self.dcm_lvl, dcm_lvl_dfs = self.dcm_lvl_res)

                    # save related files
                    mod_related_files_save(self.mod, self.study_json, self.in_img, self.out, 
                                           **kwargs
                                           )








# modality output set
def mod_save(img_type, mod, sufx, input_img, bids_name, dcm_lvl = 0, **kwargs):
    bids_dir = os.path.dirname(bids_name)
    bids_base = os.path.basename(bids_name).split('.')[0]
    bids_out = f'{bids_dir}/{bids_base}'


    # nii
    if img_type == 'nii':
        # save it as nii.gz bids
        if not os.path.exists(f'{bids_out}.nii.gz'):
            nii_img = nib.load(input_img)
            nib.save(nii_img, f'{bids_out}.nii.gz')
            # subprocess.run([
            #     'mrconvert',
            #     '-info',
            #     f'{input_img}',
            #     f'{bids_out}.nii.gz'
            # ])


    # nii.gz
    elif img_type == 'nii.gz':
        # save it as nii.gz bids
        if not os.path.exists(f'{bids_out}.nii.gz'):
            shutil.copyfile(input_img, f'{bids_out}.nii.gz')


    # dcm
    elif img_type == 'dcm':
        if dcm_lvl == 0:
            if not os.path.exists(f'{bids_out}.nii.gz'):
                subprocess.run([
                    'dcm2niix', 
                    '-b', 'y',
                    '-z', 'y',
                    '-w', '0',
                    '-o', f'{bids_dir}',
                    '-f', f'{bids_base}',
                    f'{input_img}',
                    ])


        else:
            if 'dcm_lvl_dfs' in kwargs and kwargs.get('dcm_lvl_dfs') is not None:
                dcm_lvl_hier = kwargs.get('dcm_lvl_dfs')


                # dwi uses mrtrix3 mrconvert to use .mif file
                if mod == 'dwi':
                    if sufx == 'dwi':
                        dcm_hierc = (dcm_lvl_hier
                                    .query("modality == 'dwi' & suffix_tracer == 'dwi'")
                                    .iloc[0]
                                    ['response']
                                    )


                        if not os.path.exists(f'{bids_out}.mif'):
                            dcmd = f'echo {dcm_hierc} | mrconvert -info -export_grad_fsl {bids_out}.bvec {bids_out}.bval -json_export {bids_out}.json {input_img} {bids_out}.mif'
                            subprocess.call(dcmd, shell=True)

                            # create a symbolic link to work with bids spec
                            os.symlink(f'{bids_out}.mif', f'{bids_out}.nii.gz')


                    elif sufx == 'dwi_rev_b0':
                        dcm_hierc = (dcm_lvl_hier
                                    .query("modality == 'dwi' & suffix_tracer == 'dwi_rev_b0'")
                                    .iloc[0]
                                    ['response']
                                    )


                        if not os.path.exists(f'{bids_out}.mif'):
                            dcmd = f'echo {dcm_hierc} | mrconvert -info -json_export {bids_out}.json {input_img} {bids_out}.mif'
                            subprocess.call(dcmd, shell=True)

                            # create a symbolic link to work with bids spec
                            os.symlink(f'{bids_out}.mif', f'{bids_out}.nii.gz')

                
                # need to create all the rest of possibilities

                # else:
                #     dcm_hierc = (dcm_lvl_hier
                #                 .query("modality == dwi & suffix_tracer == 'dwi'")
                #                 .iloc[0]
                #                 ['response']
                #                 )


                #     if not os.path.exists(f'{bids_out}.nii.gz'):
                #         subprocess.run([
                #             'echo',
                #             f'{dcm_hierc}',
                #             '|',
                #             'mrconvert',
                #             '-info',
                #             '-json_export',
                #             f'{bids_out}.json',
                #             f'{input_img}',
                #             f'{bids_out}.nii.gz'
                #         ])

    print('\n')





# related modality output save
def mod_related_files_save(mod, jsonfile, input_img, bids_name, **kwargs):
    # variables
    input_base, bids_base = os.path.basename(input_img).split('.')[0], os.path.basename(bids_name).split('.')[0]
    input_dir, bids_dir = os.path.dirname(input_img), os.path.dirname(bids_name)
    input_in, bids_out = f'{input_dir}/{input_base}', f'{bids_dir}/{bids_base}'


    # related file ext dictionary
    try:
        related_files = jsonfile["modalities"][mod]["relatedfiles"]
    except KeyError as e:
        print(e)
        print(mod, jsonfile)

    else:
        if related_files is not None:
            # loop throu related files ext to check for the input and save the output
            for file_ext in related_files:
                input_file = f'{input_in}.{file_ext}'
                bids_file = f'{bids_out}.{file_ext}'
            
                # save
                if mod == "pet":
                    pass

                elif mod == 'dwi':
                    if os.path.exists(input_file) and not os.path.exists(bids_file):
                        shutil.copyfile(input_file, bids_file)
                    
                    # dwi slspect
                    if kwargs.get("slspec") is not None:
                        if file_ext == "json":
                            get_slspec(bids_file, f'{bids_out}_slspec.txt')


                elif mod == 'func':
                    f_task = kwargs.get('task') if 'task' in kwargs and kwargs.get('task') is not None else None

                    if os.path.exists(input_file) and not os.path.exists(bids_file):
                        shutil.copyfile(input_file, bids_file)

                    if f_task is not None and file_ext == "json":
                        try:
                            with open(bids_file, 'r') as ftask_json:
                                func_json_in = json.load(ftask_json)
                                func_json_in["TaskName"] = f'{f_task}'

                            with open(bids_file, 'w') as ftask_json_out:
                                json.dump(func_json_in, ftask_json_out, indent = 4)

                        except FileNotFoundError:
                            print(f"The {input_img} does not have a json file. Please, be advised.\n")
                        
                        except Exception as e:
                            print(e)
                            sys.exit(1)


                elif mod == 'fmap':
                    if os.path.exists(input_file) and not os.path.exists(bids_file):
                        shutil.copyfile(input_file, bids_file)

                    intendedfor = kwargs.get('intendedfor') if 'intendedfor' in kwargs and kwargs.get('intendedfor') is not None else None
                    intendedfor_dir = kwargs.get('intendedfor_dir') if 'intendedfor_dir' in kwargs and kwargs.get('intendedfor_dir') is not None else None
                        
                    if intendedfor is not None and intendedfor_dir is not None:
                        try:
                            with open(bids_file, 'r') as fmap_json:
                                fmap_json_in = json.load(fmap_json)
                                fmap_json_in["IntendedFor"] = f'{intendedfor_dir}/{intendedfor}.nii.gz'

                            with open(bids_file, 'w') as fmap_json_out:
                                json.dump(fmap_json_in, fmap_json_out, indent = 4)

                        except FileNotFoundError:
                            print(f"The {input_img} does not have a json file. Please, be advised.\n")
                        
                        except Exception as e:
                            print(e)
                            sys.exit(1)

    print('\n')





# sls info
## derived from the matlab code from the FSL eddy site.
def get_slspec(json_in, sls_out):
    with open(json_in, "r") as fp:
        json_data = json.load(fp)    
    
    try:
        if 'SliceTiming' not in json_data:
            print(f'We could not find "SliceTiming" information from your json file: {json_in}.\n')
            sys.exit(1)
            
        else:
            sortedslicetimes = sorted(json_data['SliceTiming'])
            sortedslicetimes, sindx = zip(*sorted(zip(json_data['SliceTiming'], range(len(json_data['SliceTiming'])))))
            mb = len(sortedslicetimes) / (sum([x != y for x, y in zip(sortedslicetimes[:-1], sortedslicetimes[1:])]) + 1)
            slspec = (np.reshape(sindx, [len(sindx) // int(mb), int(mb)]))
            np.savetxt(sls_out, slspec, delimiter=' ', fmt='%3d')
            
    except Exception as e:
        print('Something went wrong!')
        print(e)

def fix_multiecho_names(bids_dir):
    bids_path = pathlib.Path(bids_dir)

    # NIfTI files
    for f in bids_path.glob("sub-*/ses-*/func/*_e[0-9].nii.gz"):
        echo_num = f.name.split("_e")[-1].replace(".nii.gz", "")

        if f"_bold_e{echo_num}" in f.name:
            new_name = f.name.replace(
                f"_bold_e{echo_num}",
                f"_echo-{echo_num}_bold"
            )

        elif f"_sbref_e{echo_num}" in f.name:
            new_name = f.name.replace(
                f"_sbref_e{echo_num}",
                f"_echo-{echo_num}_sbref"
            )

        else:
            continue

        f.rename(f.parent / new_name)

    # JSON files
    for f in bids_path.glob("sub-*/ses-*/func/*_e[0-9].json"):
        echo_num = f.name.split("_e")[-1].replace(".json", "")

        if f"_bold_e{echo_num}" in f.name:
            new_name = f.name.replace(
                f"_bold_e{echo_num}",
                f"_echo-{echo_num}_bold"
            )

        elif f"_sbref_e{echo_num}" in f.name:
            new_name = f.name.replace(
                f"_sbref_e{echo_num}",
                f"_echo-{echo_num}_sbref"
            )

        else:
            continue

        f.rename(f.parent / new_name)

def expand_multiecho_intendedfor(bids_dir):
    bids_path = pathlib.Path(bids_dir)

    # Looking for fmaps
    for fmap_json in bids_path.glob("sub-*/ses-*/fmap/*_epi.json"):
        with open(fmap_json, "r") as f:
            data = json.load(f)

        # reading intended for
        intended = data.get("IntendedFor")

        # skipping files that have already been fixed
        if not isinstance(intended, str):
            continue
        
        # skipping dwi field maps that dont end in bold
        if not intended.endswith("_bold.nii.gz"):
            continue
        
        # locating func directory
        subject_dir = next(bids_path.glob("sub-*"))
        intended_path = subject_dir / intended
        func_dir = intended_path.parent

        print(f"Checking fmap: {fmap_json.name}")
        print(f"  IntendedFor before: {intended}")
        print(f"  func_dir: {func_dir}")

        # Case 1: IntendedFor has no run, so include all runs/echoes for that task
        if "_run-" not in intended_path.name:
            task = None
            for part in intended_path.name.split("_"):
                if part.startswith("task-"):
                    task = part.replace("task-", "")

            if task is None:
                continue

            echo_files = sorted(func_dir.glob(f"*task-{task}*_echo-*_bold.nii.gz"))
            single_files = sorted(func_dir.glob(f"*task-{task}*_bold.nii.gz"))

            all_targets = echo_files if echo_files else single_files

            if all_targets:
                data["IntendedFor"] = [
                    str(f.relative_to(subject_dir))
                    for f in all_targets
                ]
            print(f"  no-run case, task={task}")
            print(f"  echo matches: {[f.name for f in echo_files]}")
            print(f"  single matches: {[f.name for f in single_files]}")
        # Case 2: fmap already points to one run; expand that run to all echoes
        else:
            echo_pattern = intended_path.name.replace("_bold.nii.gz", "_echo-*_bold.nii.gz")
            echo_files = sorted(func_dir.glob(echo_pattern))

            if echo_files:
                data["IntendedFor"] = [
                    str(f.relative_to(subject_dir))
                    for f in echo_files
                ]

        with open(fmap_json, "w") as f:
            json.dump(data, f, indent=4)

def generate_ap_fmaps(bids_dir):
    
    bids_path = pathlib.Path(bids_dir)

    for ses_dir in bids_path.glob("sub-*/ses-*"):

        fmap_dir = ses_dir / "fmap"
        func_dir = ses_dir / "func"
        dwi_dir = ses_dir / "dwi"

        if not fmap_dir.exists():
            continue
        
        # first creating the ap map for func fmaps 
        for pa_fmap in fmap_dir.glob("*_dir-PA*_epi.nii.gz"):

            name = pa_fmap.name

            if "acq-dwi" in name:
                continue

            base = name.replace("_dir-PA", "_dir-AP")
            ap_fmap = fmap_dir / base

            # exiting if there is no ap fmap
            if ap_fmap.exists():
                continue

            # extracting the run and the task from the name
            acq = None
            run = None

            # splitting the name into separate parts delimited by _ and locating the task and run
            parts = name.split("_")
            for part in parts:
                if part.startswith("acq-"):
                    acq = part.replace("acq-","")
                if part.startswith("run-"):
                    run = part.replace("run-","")

            # exiting if there is not task
            if acq is None:
                continue
            
            # define the bold patterns for the fmap files
            bold_pattern = f"*task-{acq}*_bold.nii.gz"

            # adding the run if it exists
            if run is not None:
                bold_pattern = f"*task-{acq}*run-{run}_bold.nii.gz"

            # extracting the bolds 
            bold_files = sorted(func_dir.glob(bold_pattern))

            # returning error if there is no bold file
            if len(bold_files) == 0:
                print(f"No matching bold files found for {pa_fmap.name}")
                continue

            bold_file = bold_files[0]

            # executing fslroi as shell command in subprocess
            subprocess.run(["fslroi", str(bold_file), str(ap_fmap), "0", "3"], check=True)

            # Copy the JSON from the BOLD scan used to generate the AP fmap
            pa_json = pathlib.Path(str(pa_fmap).replace(".nii.gz", ".json"))
            ap_json = pathlib.Path(str(ap_fmap).replace(".nii.gz", ".json"))

            if pa_json.exists():
                shutil.copyfile(pa_json, ap_json)

                with open(ap_json, "r") as f:
                    data = json.load(f)

                inverse = {
                    "i": "i-",
                    "i-": "i",
                    "j": "j-",
                    "j-": "j",
                    "k": "k-",
                    "k-": "k",
                }

                data["PhaseEncodingDirection"] = inverse[data["PhaseEncodingDirection"]]

                with open(ap_json, "w") as f:
                    json.dump(data, f, indent=4)
            else:
                print(f"No matching JSON found for {bold_file.name}")
        
        # now creating ap maps for dwi fmaps
        pa_dwi_fmaps = sorted(fmap_dir.glob("*acq-dwi*_dir-PA*_epi.nii.gz"))

        if len(pa_dwi_fmaps) > 0 and dwi_dir.exists():

            dwi_files = sorted(dwi_dir.glob("*_dwi.nii.gz"))

            if len(dwi_files) > 0:
                dwi_file = dwi_files[0]

                for pa_fmap in pa_dwi_fmaps:

                    ap_fmap = pathlib.Path(str(pa_fmap).replace("_dir-PA", "_dir-AP"))

                    if ap_fmap.exists():
                        continue

                    subprocess.run(["fslroi", str(dwi_file), str(ap_fmap), "65", "7"], check=True)

                    # Copy the JSON from the DWI scan used to generate the AP fmap
                    pa_json = pathlib.Path(str(pa_fmap).replace(".nii.gz", ".json"))
                    ap_json = pathlib.Path(str(ap_fmap).replace(".nii.gz", ".json"))

                    if pa_json.exists():
                        shutil.copyfile(pa_json, ap_json)

                        with open(ap_json, "r") as f:
                            data = json.load(f)

                        inverse = {
                            "i": "i-",
                            "i-": "i",
                            "j": "j-",
                            "j-": "j",
                            "k": "k-",
                            "k-": "k",
                        }

                        data["PhaseEncodingDirection"] = inverse[data["PhaseEncodingDirection"]]

                        with open(ap_json, "w") as f:
                            json.dump(data, f, indent=4)
                    else:
                        print(f"No matching DWI JSON found for {dwi_file.name}")

        for bad_file in list(fmap_dir.glob("*.bval")) + list(fmap_dir.glob("*.bvec")):
            bad_file.unlink()     

def sanitize_jsons(bids_dir):
    bids_path = pathlib.Path(bids_dir)

    for j in bids_path.glob("sub-*/ses-*/func/*.json"):
        with open(j, "r") as f:
            data = json.load(f)

        # remove the BidsGuess
        data.pop("BidsGuess", None)

        # Usually not useful/desired for SBRef
        if "_sbref.json" in j.name:
            data.pop("SliceTiming", None)
            data.pop("AcquisitionDuration", None)

        # BOLD: keep SliceTiming unless validator complains
        if "_bold.json" in j.name:
            data.pop("AcquisitionDuration", None)

            # Only convert ms -> s if clearly wrong
            if isinstance(data.get("SliceTiming"), list) and max(data["SliceTiming"]) > 5:
                data["SliceTiming"] = [x / 1000.0 for x in data["SliceTiming"]]

        with open(j, "w") as f:
            json.dump(data, f, indent=4)

# bids convert
def create_bids(input_csv, meta_json, project, dcm_hierc, output, **kwargs):
    # Variables
    bids_dir = os.path.join(output, f"sub-{project}")
    
    # loading the json data into variables
    with open(meta_json, 'r') as jfile:
        study_json = json.load(jfile)

    # set bids specs per scan from the input_csv
    with open(input_csv) as csv_in:
        csv_reader = csv.reader(csv_in, delimiter = '\t')
        line_count = 0
        for line in csv_reader:
            if line_count == 0:
                line_count += 1
                continue
            else:
                print(f'Working on line {line_count}: {line}.')
                id = line[0]
                mod = line[1]
                sufx = line[2]
                img = line[3]

                if not os.path.exists(img):
                    print('Your input image/folder does not exist.\n')
                    
                else:
                    # session variable
                    session = None if study_json['study design']['session'] <= 1 else line[4]
                    
                    # task variable
                    if study_json['study design']['task'] is not None:
                        kwargs['task'] = line[5]
                    elif mod == 'func' and sufx == 'bold':
                        kwargs['task'] = 'rest'
                    
                    # run variable
                    kwargs['run'] = None if study_json['study design']['run'] is None else line[6]

                    # dir variable 
                    kwargs['dir'] = line[7] if len(line) > 7 and line[7] not in (None, "") else None

                    # rec variable
                    kwargs['rec'] = None if study_json['study design']['rec'] is None else line[8]

                    # recording variable
                    kwargs['recording'] = None if study_json['study design']['recording'] is None else line[9]
            
                    # pet tracer variable
                    kwargs['ancil'] = line[10] if mod == "pet" or mod == "fmap" else None

                    # BIDS time
                    subjimg = img2bids(id, mod, sufx)

                    # BIDS setup
                    subjimg.setup(bids_dir, ses=session)

                    # convert2bids
                    subjimg.convert(img, 
                                    meta_json,
                                    dcm_hierc,
                                    **kwargs
                                    )

                line_count += 1

    # Fix the echo naming
    fix_multiecho_names(bids_dir)

    # Fix the multiecho intended fors
    expand_multiecho_intendedfor(bids_dir)

    # Generate dervied AP fmaps after all the scans are converted
    generate_ap_fmaps(bids_dir)

    # Sanitize the jsons
    sanitize_jsons(bids_dir)

    # BIDS dataset description json
    db_json = {
        "Name": project,
        "BIDSVersion": "1.8.0",
        "DatasetType": "raw"
    }
    with open(f'{bids_dir}/dataset_description.json', 'w') as jfile:
        json.dump(db_json, jfile, indent = 4)


    # BIDS derivatives dataset json for brain mask
    with open(input_csv) as csv_in:
        csv_reader = csv.reader(csv_in, delimiter = '\t')
        user_mask = any("mask" in row[2].lower() or "masks" in row[2].lower() for row in csv_reader if len(row) >= 3)
        if user_mask:
            der_json = {
                "Name": project,
                "BIDSVersion": "1.8.0",
                "DatasetType": "derivative",
                "GeneratedBy": [
                    {
                        "Name": "brain_mask",
                        "Description": "User provided brain mask."
                    }
                ]
            }

            with open(f'{bids_dir}/derivatives/brain_mask/dataset_description.json', 'w') as jfile:
                json.dump(der_json, jfile, indent = 4)


    if kwargs.get("slspec") is not None:
        # .bidsigore file
        bids_path = pathlib.Path(bids_dir)
        slspecs = bids_path.glob('**/*_slspec.txt')
        slspec_files = [file for file in slspecs if file]

        if len(slspec_files) > 0:
            bidsignore = f'{bids_dir}/.bidsignore'
            with open(bidsignore, 'w') as fh:
                fh.writelines('*_slspec.txt')


