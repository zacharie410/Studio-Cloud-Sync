import requests
import json
import os
import time
import argparse  # Import argparse module for CLI arguments
from dotenv import load_dotenv
# Load the .env file
load_dotenv()
apiKey = os.getenv('apiKey', '')

# Load configuration from JSON file
def load_config():
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
        return config

config = load_config()

# Extract values from the loaded configuration
universeId = config.get('universeId', '')
placeId = config.get('placeId', '')
verion_control_name_whitelist = config.get('verion_control_name_whitelist', [])

# Headers and Endpoints
apiKeyHeaderKey = "x-api-key"

instanceId = "root"
headers = {apiKeyHeaderKey: apiKey}

listChildrenUrl = "https://apis.roblox.com/cloud/v2/universes/%s/places/%s/instances/%s:listChildren"
getOperationUrl = "https://apis.roblox.com/cloud/v2/%s"

numberOfRetries = 10
retryPollingCadence = 5

doneJSONKey = "done"


# Create the directory for .lua files if it doesn't exist
lua_files_dir = "ScriptExplorer"
if not os.path.exists(lua_files_dir):
    os.makedirs(lua_files_dir)

instance_mapping = {}

def ListChildren():
    url = listChildrenUrl % (universeId, placeId, instanceId)
    headerData = {apiKeyHeaderKey: apiKey}
    results = requests.get(url, headers=headerData)
    return results

def GetOperation(operationPath):
    url = getOperationUrl % (operationPath)
    headerData = {apiKeyHeaderKey: apiKey}
    results = requests.get(url, headers=headerData)
    return results

def PollForResults(operationPath):
    currentRetries = 0
    while currentRetries < numberOfRetries:
        time.sleep(retryPollingCadence)
        results = GetOperation(operationPath)
        currentRetries += 1

        if results.status_code != 200 or results.json()[doneJSONKey]:
            return results

def list_and_create_scripts(parent_id="root", parent_name="root"):
    response = requests.get(listChildrenUrl % (universeId, placeId, parent_id), headers=headers)
    if response.status_code != 200:
        print("Failed to list instances:", response.text)
        return
    operationPath = response.json()['path']
    response = PollForResults(operationPath)
    children = response.json()['response']['instances']
    for child in children:
        is_container = child["hasChildren"] == True
        child = child["engineInstance"]
        instance_type = child["Details"]
        instance_type_name = ""
        if instance_type.get("Script"):
            instance_type_name = "Script"
        elif instance_type.get("LocalScript"):
            instance_type_name = "LocalScript"
        elif instance_type.get("ModuleScript"):
            instance_type_name = "ModuleScript"
        instance_type = instance_type.get(instance_type_name)

        if instance_type:
            instance_id = child["Id"]
            instance_name = child["Name"]
            file_name = f"{parent_name}_{instance_name}-{instance_type_name}_{instance_id}.lua"
            file_path = os.path.join(lua_files_dir, file_name)
            with open(file_path, 'w', encoding='utf-8') as file:
                file_content = instance_type.get("Source")
                file.write(file_content)

            instance_mapping[instance_id] = {
                "name": instance_name,
                "type": instance_type_name,
                "file_path": file_path
            }

        if is_container and (instance_type and instance_type.get("Folder") or child["Name"] in verion_control_name_whitelist):
            list_and_create_scripts(parent_id=child["Id"], parent_name=child["Name"])

def update_datamodel():
    list_and_create_scripts()
    with open("instance_mapping.json", 'w', encoding='utf-8') as json_file:
        json.dump(instance_mapping, json_file, indent=4)
    print(f"Created {len(instance_mapping)} .lua files and updated mapping.")

updateInstanceUrl = "https://apis.roblox.com/cloud/v2/universes/%s/places/%s/instances/%s"
contentTypeHeaderKey = "Content-type"
contentTypeHeaderValue = "application/json"
detailsJSONKey = "Details"
engineInstanceJSONKey = "engineInstance"

def GeneratePostData(type, source_code):
    propertiesDict = {"Source": source_code}
    detailsDict = {type: propertiesDict}
    instanceDict = {detailsJSONKey: detailsDict}
    outerDict = {engineInstanceJSONKey: instanceDict}
    return json.dumps(outerDict)

import requests

def UpdateInstance(postData, updateId):
    try:
        # Assuming universeId, placeId, updateInstanceUrl, apiKeyHeaderKey, apiKey, 
        # contentTypeHeaderKey, and contentTypeHeaderValue are defined elsewhere
        url = updateInstanceUrl % (universeId, placeId, updateId)
        headerData = {apiKeyHeaderKey: apiKey, contentTypeHeaderKey: contentTypeHeaderValue}
        
        # Perform the PATCH request
        result = requests.patch(url, headers=headerData, data=postData)
        result.raise_for_status()  # This will raise an HTTPError if the response was an error

    except KeyError as e:
        print(f"KeyError: The script might be open in studio, missing key: {e}")
        result = None  # or set a default result or handle it in another way

    except requests.exceptions.RequestException as e:
        # Handle any errors from the requests library
        print(f"RequestException: Error making request to {url}, Error: {e}")
        result = None

    except Exception as e:
        # Catch-all for any other exceptions
        print(f"An unexpected error occurred: {e}")
        result = None

    return result


folder_path = 'roblox_lua_files'

def get_current_files():
    try:
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        return {f: os.path.getmtime(os.path.join(folder_path, f)) for f in files}
    except Exception as e:
        print(f"Error accessing folder: {e}")
        return {}
    
def save_file(fileName, file):
    data = file.read()
    id = fileName[-40:-4]
    result = UpdateInstance(GeneratePostData(instance_mapping[id]["type"], data), id)
    print(f"Updated {fileName}: {result.status_code}")

def save_all_files():
    current_files = get_current_files()
    for f, mtime in current_files.items():
        with open(os.path.join(folder_path, f), 'r') as file:
            save_file(f, file)

def monitor_and_save_changes(loop=False, timer=3):
    changes = get_current_files()
    do_run=True
    while do_run:
        current_files = get_current_files()
        for f, mtime in current_files.items():
            if f not in changes or changes[f] < mtime:
                changes[f] = mtime
                with open(os.path.join(folder_path, f), 'r') as file:
                    save_file(f, file)

        for f in list(changes.keys()):
            if f not in current_files:
                del changes[f]
        
        do_run=loop
        time.sleep(timer)

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Roblox Lua Script Manager")
parser.add_argument("-pull", help="Update the data model and .lua files", action="store_true")
parser.add_argument("-push", help="Update the data model and .lua files", action="store_true")
parser.add_argument("-monitor", help="Monitor changes and update .lua files as needed", action="store_true")

args = parser.parse_args()
map_path = "./instance_mapping.json"

def main():
    global instance_mapping
    # Check if the file exists
    if not os.path.exists(map_path):
        # If the file doesn't exist, create it and initialize with an empty dictionary
        with open(map_path, 'w') as f_out:
            json.dump({}, f_out)  # You can replace {} with your desired default content

    # Now that the file exists for sure, open it and load its content
    with open(map_path, 'r') as f_in:
        instance_mapping = json.load(f_in)
    
    if args.pull:
        print("Pull request . . .")
        update_datamodel()
        print("Pull request complete")

    elif args.push:
        print("Push request . . .")
        save_all_files()
        print("Push request complete")
    elif args.monitor:
        print("Watching files . . .")
        monitor_and_save_changes(loop=True)
        print("Stopped watching files")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
