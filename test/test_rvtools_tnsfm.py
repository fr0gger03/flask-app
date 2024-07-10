import pandas as pd
from pandas import testing as pdtest
from ..src.transform_rvtools import rvtools_conversion

def test_lova_transform():
    target_df = pd.read_csv('target_csv_file')

    file_name = 'source_rvtools_file'
    input_path = 'test/'
    describe_params = {"file_name":file_name, "input_path":input_path}
    source_df = pd.DataFrame(rvtools_conversion(**describe_params))

    pdtest.assert_frame_equal(source_df,target_df)