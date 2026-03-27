
import os
import json

# Define the directories
input_dir  = "/home/mo3/webplots/config/resatmc_expver1"
output_dir = "."

# Ensure the output directory exists
os.makedirs(output_dir, exist_ok=True)

# Process each file in the input directory
for filename in os.listdir(input_dir):
    if filename.endswith(".json"):
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        # Read the JSON file
        with open(input_path, 'r') as infile:
            try:
                data = json.load(infile)
                with open(output_path, 'w') as outfile:
                    json.dump(data, outfile, indent=4)
            except json.JSONDecodeError:
                print(f"Error decoding JSON in file: {filename}")
