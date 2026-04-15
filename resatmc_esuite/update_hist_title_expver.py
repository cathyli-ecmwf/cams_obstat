import json
from pathlib import Path

new_expver = "0080"
OLD_LINE = "Exp=$expver  LAST TIME WINDOW ($last_time)"
NEW_LINE = f"Exp={new_expver}  LAST TIME WINDOW ($last_time)"

for json_file in Path(".").glob("hist*.json"):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    titles = data.get("inline_plot_structure", {}).get("variable_title")

    if isinstance(titles, list):
        updated = False
        for i, line in enumerate(titles):
            if line == OLD_LINE:
                titles[i] = NEW_LINE
                updated = True

        if updated:
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"Updated: {json_file}")
