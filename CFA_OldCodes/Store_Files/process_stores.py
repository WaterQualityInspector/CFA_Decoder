import json
import sys


if __name__ == "__main__":
    if "-stores" in sys.argv:
        store_file = sys.argv[sys.argv.index("-stores") + 1]
    else:
        store_file = "all_stores.json"
    with open(store_file) as f:
        js = f.read()
        stores = json.loads(js)
    
    drive_through_locations = {}
    dine_in_locations = {}
    for store, types in stores.items():
        if "02" in types:
            drive_through_locations[store] = {"02": types["02"]}
        if "01" in types:
            dine_in_locations[store] = {"01": types["01"], "03": types["03"]}
    
    with open("all_drive_through.json", "w+") as f:
        output = json.dumps(drive_through_locations, sort_keys=True, indent=4)
        f.write(output)
    with open("all_dine_in.json", "w+") as f:
        output = json.dumps(dine_in_locations, sort_keys=True, indent=4)
        f.write(output)