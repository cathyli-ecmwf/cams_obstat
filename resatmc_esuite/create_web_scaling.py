#############################################################
# python3 script to  create scales for on demand web json
#############################################################
#Usage
import os, sys
import netCDF4 as nc
import numpy as np
import json
import argparse
import builtins
import re
import math

def get_parser():
    """Get a command-line argument parser for the program."""

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument("-j","--injson", type=str, default="none",required=True,
                        help=("input json"))

    parser.add_argument("-o","--outjson", type=str, default="-1",required=False,
                        help=("Output json"))

    parser.add_argument("-i","--inputdata", type=str, default="-1",required=False,
                        help=("input netcdf"))

    parser.add_argument("-m","--mode", type=str, default="geo",required=False,
                        help=("netcdf type"))

    parser.add_argument("-g","--update_json_only", action='store_true', default=False,  help=("update json file only"))

    parser.add_argument("-t","--margin", type=str, default="10",required=False,
                        help=("input netcdf"))

    return parser

def build_range(center_val, min_val, max_val, steps):
    if min_val < center_val < max_val:
        # Compute step size
        total_steps = steps - 1  
        step_size = (max_val - min_val) / total_steps

        levels = np.arange(min_val, max_val + step_size, step_size)

        if center_val not in levels:
            levels = np.sort(np.append(levels, center_val))

        below_center = levels[levels < center_val]
        above_center = levels[levels > center_val]

        # Recalculate based on the step size
        levels = np.concatenate((
            np.arange(min_val, center_val, step_size),
            [center_val],
            np.arange(center_val + step_size, max_val + step_size, step_size)
        ))
    else:
        levels = np.linspace(min_val, max_val, steps)

    return {
        "contour_min_level": float(round(min_val, 2)),
        "contour_max_level": float(round(max_val, 2)),
        "contour_levels": [float(round(level, 2)) for level in levels]
    }

def build_minmax(var_name,min_val, max_val):
    """
    Return the min and max values rounded to 2 decimal places.
    """
    if "count" in var_name:
      min_val=0.0
    return [float(round(min_val, 2)), float(round(max_val, 2))]

def add_margin(min_val, max_val, margin_percent=10):
    range_val = max_val - min_val
    margin = range_val * (margin_percent / 100)
    new_min = min_val - margin
    new_max = max_val + margin
    return new_min, new_max

def generate_scaling(var_names):
  scaling_data = {}

  global_min = {}
  global_max = {}

  for inc in range(len(ncfiles)):
   ncfile=ncfiles[inc]
   if "count" in var_names[0] and inc!=0:
       continue
   with nc.Dataset(ncfile, "r") as ds:
        # Read coordinate variables
    level_values = ds.variables["level"][:]
    flag_values = ds.variables["flag"][:]
    area_values = ds.variables["area"][:]
    lpress=("hPa" in ds.variables["level"][0])
    lmerge=False
    if nctype=="hovlev":
     lmerge=True

    if np.issubdtype(level_values.dtype, np.number):  # Check if numeric
     level_values = level_values.astype(int)

    for ivar in range(len(var_names)):
     var_name=var_names[ivar]
     if "count" in var_names[ivar]:
      var_name="count"
     try:
      dimensions = ds.variables[var_name].dimensions
      flag_dim_index = dimensions.index("flag")
      area_dim_index = dimensions.index("area")
      level_dim_index = dimensions.index("level")
     except:
      pass

    all_data = {var: ds.variables[var][:] for var in ds.variables}
    for flag_idx, flag_value in enumerate(flag_values):
        if flag_value not in global_min:
          global_min[flag_value]={}
          global_max[flag_value]={}
        flag_key = f"flag:{flag_value}"
     #   if flag_value != "Used":
     #       continue
        scaling_data[flag_key] = {}

        for area_idx, area_value in enumerate(area_values):
            #if area_value != "Globe":
            #    continue
            if area_value not in global_min[flag_value]:
             global_min[flag_value][area_value]={}
             global_max[flag_value][area_value]={}
            area_key = f"area:{area_value}"
            scaling_data[flag_key][area_key] = {}
            if lmerge:
              global_min[flag_value][area_value][0]=np.inf
              global_max[flag_value][area_value][0]=-np.inf
            
            if lmerge:
                for var_name in var_names:
                    var_name = var_name.strip()
                    try:
                        # Extract data for the current variable and indices
                       slice_obj = [slice(None)] * len(dimensions) 
                       if lmerge:
                        slice_obj[flag_dim_index] = flag_idx
                        slice_obj[area_dim_index] = area_idx
                        data_slice = all_data[var_name][tuple(slice_obj)]
                        data_slice=data_slice[data_slice>-9000]
                        percentile_95 = np.percentile(data_slice, 95)
                        data_slice = data_slice[data_slice <= percentile_95]

                        # Handle masked values and missing data
                        if np.ma.is_masked(data_slice):
                            data_slice = data_slice.compressed()

                        if data_slice.size == 0:
                            continue  # Skip empty slices

                        # Update global min/max across all variables
                        global_min[flag_value][area_value][0] = \
                                builtins.min(global_min[flag_value][area_value][0], np.min(data_slice))
                        global_max[flag_value][area_value][0] = \
                                builtins.max(global_max[flag_value][area_value][0], np.max(data_slice))


                    except IndexError:
                        print(f"Skipping invalid combination: var={var_name}, level={0}, flag={flag_value}, area={area_value}")

            else:

             for level_idx, level_value in enumerate(level_values):
                #if level_idx != 5:
                #    continue

                if level_value not in global_min[flag_value][area_value]:
                    global_min[flag_value][area_value][level_value]=np.inf
                    global_max[flag_value][area_value][level_value]=-np.inf


                for var_name in var_names:
                    var_name = var_name.strip()
                    if "count" in var_name:
                      var_name="count"
                    try:
                        # Extract data for the current variable and indices
                        slice_obj = [slice(None)] * len(dimensions) 
                        slice_obj[flag_dim_index] = flag_idx
                        slice_obj[area_dim_index] = area_idx
                        slice_obj[level_dim_index] = level_idx
                        data_slice = all_data[var_name][tuple(slice_obj)]
                        data_slice=data_slice[data_slice>-9000]
                        percentile_95 = np.percentile(data_slice, 95)
                        data_slice = data_slice[data_slice <= percentile_95]

                        # Handle masked values and missing data
                        if np.ma.is_masked(data_slice):
                            data_slice = data_slice.compressed()

                        if data_slice.size == 0:
                            continue  # Skip empty slices

                        # Update global min/max across all variables

                        global_min[flag_value][area_value][level_value] = \
                                builtins.min(global_min[flag_value][area_value][level_value], np.min(data_slice))
                        global_max[flag_value][area_value][level_value] = \
                                builtins.max(global_max[flag_value][area_value][level_value], np.max(data_slice))

                    except IndexError:
                        print(f"Skipping invalid combination: var={var_name}, level={level_value}, flag={flag_value}, area={area_value}")

  for flag_value in global_min:
      flag_key = f"flag:{flag_value}"
      for area_value in global_min[flag_value]:
          area_key = f"area:{area_value}"
          if lmerge:
              if global_min[flag_value][area_value][0] == np.inf or global_max[flag_value][area_value][0] == -np.inf:
                  continue
              glo_min, glo_max = \
                   add_margin(global_min[flag_value][area_value][0], global_max[flag_value][area_value][0], margin)

              # If valid data was found, store the min/max for the current level
              if glo_min != np.inf and glo_max != -np.inf:
                    scaling_data[flag_key][area_key] = build_minmax(var_name,glo_min, glo_max)
          else:
           for level_value in global_min[flag_value][area_value]:
              if global_min[flag_value][area_value][level_value] == np.inf or global_max[flag_value][area_value][level_value] == -np.inf:
                  continue
              glo_min, glo_max = \
                   add_margin(global_min[flag_value][area_value][level_value], global_max[flag_value][area_value][level_value], margin)

              # If valid data was found, store the min/max for the current level
              if glo_min != np.inf and glo_max != -np.inf:
                    level_key = f"level:{level_value}"
                    scaling_data[flag_key][area_key][level_key] = build_minmax(var_name,glo_min, glo_max)

  return scaling_data


parser = get_parser()
args = parser.parse_args(sys.argv[1:])

input_json = args.injson
output_scales_json = args.outjson
nctype = args.mode
margin = int(args.margin)
update_json=args.update_json_only

ncfiles = args.inputdata.split()
try:
 for i in range(len(ncfiles)):
  ncfiles[i]=str(ncfiles[i])
except:
 pass

if update_json:
 print(input_json)
 try:
    with open(input_json, "r", encoding="utf-8") as f:
     raw_content = f.read()
 except json.JSONDecodeError as e:
    print(f"Error loading original JSON: {e}")
    exit(1)

 with open(input_json, 'r') as file:
     original_data = json.load(file)

 if isinstance(original_data.get('layers'), list):
    for layer in original_data['layers']:  # Iterate through each dictionary in the list
        if isinstance(layer.get('values', {}).get('level'), str) and 'hPa' in layer['values']['level']:
            layer['values']['level'] = layer['values']['level'].replace(".", "@")

 variables_block = original_data.get("variables", None)

 for variable in original_data.get("variables", []):
  if "values" in variable:
   # Check if any value contains "hPa"
   if any("hPa" in str(val) for val in variable["values"]):
     # Create the "labels" field with "." replaced by "@"
     variable["values"] = [val.replace(".", "@") for val in variable["values"]]
     variable["labels"] = [val.replace("@", ".") for val in variable["values"]]

 # Save the updated JSON
 try:
    with open(output_scales_json, "w") as updated_file:
        json.dump(original_data, updated_file, indent=4)
    print(f"Updated JSON saved to {output_scales_json}")
 except Exception as e:
    print(f"Error saving updated JSON: {e}")
 exit(0)

if nctype in ["geo","hov","hovlev"]:
 global_min = {}
 global_max = {}
 steps = 19
 list_variables=[]
 for inc in range(len(ncfiles)):
  ncfile=ncfiles[inc]
  with nc.Dataset(ncfile, "r") as ds:
        # Read coordinate variables
    start_processing = False
    level_values = ds.variables["level"][:]
    flag_values = ds.variables["flag"][:]
    lpress=("hPa" in ds.variables["level"][0])
    lmerge=False
    if nctype=="hovlev":
     lmerge=True
    if np.issubdtype(level_values.dtype, np.number):  # Check if numeric
     level_values = level_values.astype(int)

    variables=[]
    for var_name in ds.variables:
     if var_name not in ["area","North","South","West","East"]  and len(ds.variables[var_name].dimensions)>1:
      variables.append(var_name)

    all_data = {var: ds.variables[var][:] for var in variables}

    for flag_idx, flag_value in enumerate(flag_values):
     for var_name in ds.variables:
        if not start_processing or var_name in ["area","North","South","West","East"] or "andep" in var_name or len(ds.variables[var_name].dimensions)==1:
            # Set the flag to True once we reach the "count" variable
            if var_name == "count":
                start_processing = True
            if not start_processing or var_name in ["area","North","South","West","East"] or "andep" in var_name or len(ds.variables[var_name].dimensions)==1:
              continue
        variable = ds.variables[var_name]
        dimensions = variable.dimensions
        level_idx = dimensions.index("level")
        levels = variable.shape[level_idx]

        if flag_value not in global_min:
         global_min[flag_value]={}
         global_max[flag_value]={}

        if var_name not in global_min[flag_value]:
         global_min[flag_value][var_name]={}
         global_max[flag_value][var_name]={}
         if lmerge:
           global_min[flag_value][var_name][0] = np.inf
           global_max[flag_value][var_name][0] = -np.inf
         else:
           for i in range(levels):
            global_min[flag_value][var_name][i] = np.inf
            global_max[flag_value][var_name][i] = -np.inf

        data = all_data[var_name]
        if np.ma.is_masked(data):  # Check if it's a masked array
           if data.count() == 0:  # All values are missing
               continue
        elif np.all(data == getattr(variable, "_FillValue", np.nan)):
           continue

        flag_dim_index = dimensions.index("flag")
        if lmerge:
          slice_obj = [slice(None)] * len(dimensions) 
          slice_obj[flag_dim_index] = flag_idx
          data_slice = all_data[var_name][tuple(slice_obj)]
          data_slice=data_slice[data_slice>-9000]
          i=0
          global_min[flag_value][var_name][i] = builtins.min(global_min[flag_value][var_name][i], np.min(data_slice))
          global_max[flag_value][var_name][i] = builtins.max(global_max[flag_value][var_name][i], np.max(data_slice))
          if global_min[flag_value][var_name][i] < 0 and global_max[flag_value][var_name][i] > 0:
           symmetric_range = builtins.max(abs(global_min[flag_value][var_name][i]), abs(global_max[flag_value][var_name][i]))
           global_min[flag_value][var_name][i] = -symmetric_range
           global_max[flag_value][var_name][i] = symmetric_range
        else:
          if "level" in dimensions:
            level_idx = dimensions.index("level")
            levels = variable.shape[level_idx]

            # Iterate through each level and compute min/max and step size
            for i in range(levels):
                # Dynamically slice along the "level" dimension
                slice_obj = [slice(None)] * len(dimensions)  # Default slice for all dimensions
                slice_obj[level_idx] = i  # Set slice for the level dimension
                slice_obj[flag_dim_index] = flag_idx
                data_slice = all_data[var_name][tuple(slice_obj)]
                data_slice=data_slice[data_slice>-9000]

                # Handle masked values
                if np.ma.is_masked(data_slice):
                    data_slice = data_slice.compressed()  # Remove masked values
                else:
                    data_slice = data_slice[:]

                if data_slice.size == 0:  # If the slice is empty after compression
                    continue

                global_min[flag_value][var_name][i] = builtins.min(global_min[flag_value][var_name][i], np.min(data_slice))
                global_max[flag_value][var_name][i] = builtins.max(global_max[flag_value][var_name][i], np.max(data_slice))
                if global_min[flag_value][var_name][i] < 0 and global_max[flag_value][var_name][i] > 0:
                 symmetric_range = builtins.max(abs(global_min[flag_value][var_name][i]), abs(global_max[flag_value][var_name][i]))
                 global_min[flag_value][var_name][i] = -symmetric_range
                 global_max[flag_value][var_name][i] = symmetric_range

 output_scales = {}
 for flag_value  in global_min:
  output_scales[f"flag:{flag_value}"] = {}
  for var_name in global_min[flag_value]:
    output_scales[f"flag:{flag_value}"][f"data_type:{var_name}"] = {}

    for level_idx in global_min[flag_value][var_name]:
       scaling = build_range(0.0,global_min[flag_value][var_name][level_idx], global_max[flag_value][var_name][level_idx], steps)
       if not  math.isinf(global_min[flag_value][var_name][level_idx]) and not  math.isinf(global_max[flag_value][var_name][level_idx]):
        if lmerge:
         output_scales[f"flag:{flag_value}"][f"data_type:{var_name}"] = {
                  "contour_level_count": steps,
                  "contour_min_level": scaling["contour_min_level"],
                  "contour_max_level": scaling["contour_max_level"]
           }
        elif lpress:
         output_scales[f"flag:{flag_value}"][f"data_type:{var_name}"][f"level:{level_values[level_idx]}"] = {
            "contour_level_count": steps,
            "contour_min_level": scaling["contour_min_level"],
            "contour_max_level": scaling["contour_max_level"]
         }
        else:
         output_scales[f"flag:{flag_value}"][f"data_type:{var_name}"][f"level:{level_idx+1}"] = {
            "contour_level_count": steps,
            "contour_min_level": scaling["contour_min_level"],
            "contour_max_level": scaling["contour_max_level"]
         }
    if "fgdep" in var_name:
     andep_var_name=var_name.replace("fgdep","andep")
     output_scales[f"flag:{flag_value}"][f"data_type:{andep_var_name}"] = {}
     for level_idx in global_min[flag_value][var_name]:
       scaling = build_range(0.0,global_min[flag_value][var_name][level_idx], global_max[flag_value][var_name][level_idx], steps)
       if not  math.isinf(global_min[flag_value][var_name][level_idx]) and not  math.isinf(global_max[flag_value][var_name][level_idx]):
        andep_var_name=var_name.replace("fgdep","andep")
        if lmerge:
         output_scales[f"flag:{flag_value}"][f"data_type:{andep_var_name}"] = {
                      "contour_level_count": steps,
                      "contour_min_level": scaling["contour_min_level"],
                      "contour_max_level": scaling["contour_max_level"]
                    }
        elif lpress:
         output_scales[f"flag:{flag_value}"][f"data_type:{andep_var_name}"][f"level:{level_values[level_idx]}"] = {
           "contour_level_count": steps,
           "contour_min_level": scaling["contour_min_level"],
           "contour_max_level": scaling["contour_max_level"]
           }
        else:
         output_scales[f"flag:{flag_value}"][f"data_type:{andep_var_name}"][f"level:{level_idx + 1}"] = {
           "contour_level_count": steps,
           "contour_min_level": scaling["contour_min_level"],
           "contour_max_level": scaling["contour_max_level"]
         }


 try:
   with open(input_json, "r", encoding="utf-8") as f:
     raw_content = f.read()
   original_data = json.loads(raw_content)
 except json.JSONDecodeError as e:
   print(f"Error loading original JSON: {e}")
   exit(1)

 # Load the created JSON
 with open(output_scales_json, "w") as updated_file:
    json.dump({"example_key": "example_value"}, updated_file, indent=4)

 page_structure = original_data.get("page_structure", None)

 if isinstance(original_data.get('layers'), list):
    for layer in original_data['layers']:  # Iterate through each dictionary in the list
        if isinstance(layer.get('values', {}).get('level'), str) and 'hPa' in layer['values']['level']:
            layer['values']['level'] = layer['values']['level'].replace(".", "@")

 for variable in original_data.get("variables", []):
  if "values" in variable:
   # Check if any value contains "hPa"
   print(variable["values"])
   if any("hPa" in str(val) for val in variable["values"]):
 #    # Create the "labels" field with "." replaced by "@"
     variable["values"] = [val.replace(".", "@") for val in variable["values"]]
     variable["labels"] = [val.replace("@", ".") for val in variable["values"]]

 # Navigate to "page_structure" within "inline_plot_structure"
 inline_plot_structure = original_data.get("inline_plot_structure", None)

 if inline_plot_structure is None:
    print("'inline_plot_structure' key not found in the JSON.")
    exit(1)

 page_structure = inline_plot_structure.get("page_structure", None)

 if page_structure is None:
    print("'page_structure' key not found in 'inline_plot_structure'.")
    exit(1)

 # Replace "common_legend" in the page structure
 updated = False
 for page in page_structure:
    page["common_legend"] = output_scales
    # if "common_legend" in page:

else:
 print(input_json)
 try:
    with open(input_json, "r", encoding="utf-8") as f:
     raw_content = f.read()
 except json.JSONDecodeError as e:
    print(f"Error loading original JSON: {e}")
    exit(1)

 with open(input_json, 'r') as file:
     original_data = json.load(file)

 if isinstance(original_data.get('layers'), list):
    for layer in original_data['layers']:  # Iterate through each dictionary in the list
        if isinstance(layer.get('values', {}).get('level'), str) and 'hPa' in layer['values']['level']:
            layer['values']['level'] = layer['values']['level'].replace(".", "@")

 for variable in original_data.get("variables", []):
  if "values" in variable:
   # Check if any value contains "hPa"
   if any("hPa" in str(val) for val in variable["values"]):
     # Create the "labels" field with "." replaced by "@"
     variable["values"] = [val.replace(".", "@") for val in variable["values"]]
     variable["labels"] = [val.replace("@", ".") for val in variable["values"]]

 inline_plot_structure = original_data.get("inline_plot_structure", None)

 page_structure = inline_plot_structure.get("page_structure", None)

 for entry in page_structure:
  if "netcdf" in entry and "variables_y" in entry["netcdf"]:
     variables_list = entry["netcdf"]["variables_y"].split(",")
     variables_list = list(filter(lambda x: x != "count_displayed", variables_list))
     scaling_json_str={}
     if variables_list != None:
      scaling_data = generate_scaling(variables_list[:])
      entry["custom_yaxis"] = scaling_data
 updated = True


# Save the updated JSON
try:
    with open(output_scales_json, "w") as updated_file:
        json.dump(original_data, updated_file, indent=4)
    print(f"Updated JSON saved to {output_scales_json}")
except Exception as e:
    print(f"Error saving updated JSON: {e}")
