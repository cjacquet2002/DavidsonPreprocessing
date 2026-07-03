###         requirements
import sys
import argparse
from datetime import datetime
import pandas as pd
from .utils.bids_transformer import create_bids




###         Main
def main(args = None):
    ###         Parse Arguments
    def parser_args():
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--input_file", required = True, help = "input csv file.")
        parser.add_argument("-s", "--meta_json", required = True, help = "study design/acquisition meta json file.")        
        parser.add_argument("-p", "--project", required = True, help = "project name.")
        parser.add_argument("-o", "--output", required = True, help = "BIDS output directory.")
        parser.add_argument("-n", "--dicom_lvl", default = 0, type = int, help = "DICOM hierarchy levels.")
        parser.add_argument('-sls', '--slspec', action = 'store_true', help = "slspec flag")


        return parser



    def parse_inputs(parser, args):
        if isinstance(args, list):
            args, unknown = parser.parse_known_args()
        return args



    if args is None:
        args = sys.argv[1:]

    
    parser = parser_args()
    args = parse_inputs(parser, args)
    args_dic = vars(args)
    start_time = datetime.now()
    keys_to_select = [ 'slspec' ]
    keywargs_args_dict = { key: args_dic[key] for key in keys_to_select if key in args_dic and args_dic[key] is not None and args_dic[key] is not False }

    # dicom hierarchy levels
    if int(args.dicom_lvl) > 0:
        input_csv = pd.read_csv(args.input_file)

        # modality list
        mod_list = (input_csv
                .pipe(lambda df_: df_.set_axis([f'col_{indx}' for indx in range(len(df_.columns))], axis='columns'))
                .query('~col_3.str.contains("nii$|nii.gz$")')
                .value_counts(subset=['col_1', 'col_2'])
                .reset_index()
                ['col_1']
                )
        

        # suffix list
        sufx_list = (input_csv
                .pipe(lambda df_: df_.set_axis([f'col_{indx}' for indx in range(len(df_.columns))], axis='columns'))
                .query('~col_3.str.contains("nii$|nii.gz$")')
                .value_counts(subset=['col_1', 'col_2'])
                .reset_index()
                ['col_2']
                )


        # inquire
        lvl_list = []
        for mod, sufx in zip(mod_list, sufx_list):
            while True:
                try:
                    dcm_lvls = input(
                        f"Please provide your DICOM hierarchy for modality: {mod} and suffix: {sufx}. If there are multiple levels, input each level with a space in between. For example, 2 4 is selecting 2 in the first level and 4 in the second level: "
                    )

                except Exception as e:
                    print("Invalid input registered.")
                    print(e)


                finally:
                    lvl_list.append(dcm_lvls)
                
                break

        
        dcm_lvl_df = (input_csv
                    .pipe(lambda df_: df_.set_axis([f'col_{indx}' for indx in range(len(df_.columns))], axis='columns'))
                    .query('~col_3.str.contains("nii$|nii.gz$")')
                    .value_counts(subset=['col_1', 'col_2'])
                    .reset_index()
                    .assign(response = lvl_list)
                    .filter(['col_1', 'col_2', 'response'])
                    .rename({'col_1': 'modality', 'col_2': 'suffix_tracer'}, axis = 'columns')
                    )
        keywargs_args_dict['dcm_lvl_df'] = dcm_lvl_df

    
    
    # BIDs conversion
    create_bids(
        args.input_file,
        args.meta_json,
        args.project,
        args.dicom_lvl,
        args.output,
        **keywargs_args_dict
    )



    ###         closing
    run_time = (datetime.now() - start_time)
    closing_msg = 'BIDS conversion is finished in {}'.format(run_time)
    print(closing_msg)




if __name__ == "__main__":
    main()

