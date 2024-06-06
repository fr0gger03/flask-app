import sys
from src.data_validation import filetype_validation
from data_transformation import lova_conversion, rvtools_conversion

def describe_import(**kwargs):
    print("Getting overview of environment.")
    input_path = kwargs['input_path']
    # ft = kwargs['file_type']
    fn = kwargs['file_name']
    output_path = "output/"

    ft = filetype_validation(input_path, fn)

    view_params = {"input_path":input_path,"file_name":fn, "output_path":output_path}

    # This section requires Python 3.10 or later.
    match ft:
        case 'live-optics':
            csv_file = lova_conversion(**view_params)
        case 'rv-tools':
            csv_file = rvtools_conversion(**view_params)

    if csv_file is not None:
        total_vms=data_describe(output_path,csv_file)
        return total_vms
    else:
        print()
        print("Something went wrong.  Please check your syntax and try again.")
        sys.exit(1)
    sys.exit(0)

def data_describe(output_path,csv_file):
    vm_data_df = pd.read_csv(f'{output_path}{csv_file}')

    # Ensure guest OS column is cast as string to better handle blank values
    vm_data_df['os'] = vm_data_df['os'].astype(str)

    total_vms = vm_data_df.vmName.count()
    print(f'\nTotal VM: {vm_data_df.vmName.count()}')
    print("\nVM Power States:")
    print(vm_data_df['vmState'].value_counts())
    print(f'\nTotal unique operating systems: {vm_data_df.os.nunique()}')
    print('\nGuest operating systems:')
    print(vm_data_df.groupby('os')['vmId'].nunique())
    print(f'\nTotal Clusters: {vm_data_df.cluster.nunique()}')
    print(f'Cluster names: {vm_data_df.cluster.unique()}')
    print(f'\nTotal vCPU: {vm_data_df.vCpu.sum()}')
    print(f'\nTotal vRAM (GiB): {vm_data_df.vRam.sum()}')
    print(f'\nTotal used VMDK (GiB): {vm_data_df.vmdkUsed.sum()}')
    print(f'\nTotal provisioned VMDK (GiB): {vm_data_df.vmdkTotal.sum()}')
    print(f'\n{vm_data_df.describe()}')
    return total_vms