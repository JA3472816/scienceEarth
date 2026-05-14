import xarray as xr
import pandas as pd
import os
import sys

def convert_nc_to_txt(nc_file_path, output_txt_path, max_file_size_mb=100):
    print(f"Loading NetCDF file: {nc_file_path}")
    try:
        ds = xr.open_dataset(nc_file_path)
    except Exception as e:
        print(f"Error loading {nc_file_path}: {e}")
        return

    dims = ds.dims
    if not dims:
        print("No dimensions found in the dataset.")
        return


    # Find the largest dimension to iterate over to save memory
    largest_dim = max(dims, key=lambda d: ds.dims[d])
    largest_dim_size = ds.dims[largest_dim]
    
    print(f"Dataset dimensions: {dict(ds.dims)}")
    print(f"Iterating over '{largest_dim}' (size: {largest_dim_size}) to minimize RAM usage...")

    max_bytes = max_file_size_mb * 1024 * 1024
    base_name, ext = os.path.splitext(output_txt_path)
    
    part_num = 1
    current_output_file = f"{base_name}_part{part_num}{ext}"
    first_chunk_in_file = True
    total_rows_written = 0
    
    # Remove existing file if any to avoid appending to old data
    if os.path.exists(current_output_file):
        os.remove(current_output_file)
    
    for i in range(largest_dim_size):
        # Select the slice
        ds_slice = ds.isel({largest_dim: i})
        
        # Convert slice to dataframe and drop missing values
        df_slice = ds_slice.to_dataframe().reset_index().dropna()
        
        if len(df_slice) > 0:
            # Write to CSV
            df_slice.to_csv(current_output_file, sep='\t', index=False, mode='a', header=first_chunk_in_file)
            first_chunk_in_file = False
            total_rows_written += len(df_slice)
            
            # Check file size after writing
            if os.path.getsize(current_output_file) > max_bytes:
                file_size_mb = os.path.getsize(current_output_file) / (1024*1024)
                print(f"Finished {current_output_file} (Size: {file_size_mb:.2f} MB)")
                part_num += 1
                current_output_file = f"{base_name}_part{part_num}{ext}"
                first_chunk_in_file = True
                if os.path.exists(current_output_file):
                    os.remove(current_output_file)
        
        # Print progress every 10%
        if (i + 1) % max(1, (largest_dim_size // 10)) == 0 or (i + 1) == largest_dim_size:
            print(f"Processed {i + 1}/{largest_dim_size} slices. Rows written: {total_rows_written}")

    # After loop, handle file renaming and cleanup
    if part_num == 1:
        if os.path.exists(current_output_file):
            if os.path.exists(output_txt_path):
                os.remove(output_txt_path)
            os.rename(current_output_file, output_txt_path)
            file_size = os.path.getsize(output_txt_path)
            print(f"Done! Generated file {output_txt_path} (Size: {file_size / (1024*1024):.2f} MB)")
        else:
            print("Done! No data was written (maybe all values were missing).")
    else:
        # If the last file is empty (e.g. exactly reached limit on previous step), remove it
        if os.path.exists(current_output_file) and os.path.getsize(current_output_file) == 0:
            os.remove(current_output_file)
            part_num -= 1
        elif os.path.exists(current_output_file):
            file_size_mb = os.path.getsize(current_output_file) / (1024*1024)
            print(f"Finished {current_output_file} (Size: {file_size_mb:.2f} MB)")
            
        print(f"Done! Files split into {part_num} parts (max ~{max_file_size_mb}MB each).")
        print(f"Total rows written across all parts: {total_rows_written}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python nc_to_txt.py <input.nc> <output.txt>")
        print("Example: python nc_to_txt.py data.nc output.txt")
        sys.exit(1)
        
    input_nc = sys.argv[1]
    output_txt = sys.argv[2]
    convert_nc_to_txt(input_nc, output_txt)