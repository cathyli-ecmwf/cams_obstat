

import os
import json


esuite_expver= "0079"

# Define the directories
input_dir  = "../resatmc_expver1"
output_dir = "."

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

# Define the key and the values to be replaced
key_to_replace = "k"
old_value = "v1"
new_value = "v2"

# Process each file in the input directory
for filename in os.listdir(input_dir):
    if filename.endswith(".json"):
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        # Read the JSON file
        with open(input_path, 'r') as infile:
            try:
                data = json.load(infile)
                data["name"]    = data["name"]+"_esuite"
                data["package"] = data["package"]+"_esuite"
                for i in range(len(data["layers"])):
                    if "values" in data["layers"][i]:
                        if not data["name"][:4] == "hist": #do not change expver 1 for timeseries! (odd)
                            data["layers"][i]["values"]["expver"] = data["layers"][i]["values"]["expver"].replace("0001",esuite_expver)
                        data["layers"][i]["values"]["label"] = data["layers"][i]["values"]["label"].replace("0001",esuite_expver)
                for i in range(len(data["variables"])):
                    if "values" in data["variables"][i]:
                        data["variables"][i]["values"]= [e.replace("0001",esuite_expver) for e in data["variables"][i]["values"]]

                # Write the modified JSON to the output directory
                with open(output_path, 'w') as outfile:
                    json.dump(data, outfile, indent=4)
            except json.JSONDecodeError:
                print(f"Error decoding JSON in file: {filename}")
