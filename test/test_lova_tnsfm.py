import pandas as pd
from pandas import testing as pdtest
from ..src.transform_lova import lova_conversion

def test_lova_transform():
    target_df = pd.read_csv('target_csv_file')

    file_name = 'source_lova_file'
    input_path = 'test/'
    describe_params = {"file_name":file_name, "input_path":input_path}
    source_df = pd.DataFrame(lova_conversion(**describe_params))

    pdtest.assert_frame_equal(source_df,target_df)