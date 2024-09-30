import pandas as pd
from pandas import testing as pdtest
from src.transform_rvtools import rvtools_conversion

def test_lova_transform():
    target_df = pd.read_csv('tests/test_files/rvtools_expected_df.csv')
    target_df['vRam'] = target_df['vRam'].astype(float)
    target_df['vmdkTotal'] = target_df['vmdkTotal'].astype(float)    

    file_name = 'rvtools_file_sample.xlsx'
    input_path = 'tests/test_files/'
    describe_params = {"file_name":file_name, "input_path":input_path}
    source_df = pd.DataFrame(rvtools_conversion(**describe_params))

    pdtest.assert_frame_equal(source_df,target_df)