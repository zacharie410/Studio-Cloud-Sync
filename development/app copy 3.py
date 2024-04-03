import argparse
import json
import os
import requests
import time
from dotenv import load_dotenv

# Load environment and configurations
load_dotenv()
config_path = 'config.json'
lua_files_dir = "ScriptExplorer"
map_path = "./instance_mapping.json"

# Initialize global variables
apiKey = os.getenv('apiKey', '')
config = {}
headers = {"x-api-key": apiKey}
contentTypeHeader = {"Content-type": "application/json"}

# API Endpoints
listChildrenUrl = "https://apis.roblox.com/cloud/v2/universes/{}/places/{}/instances/{}:listChildren"
getOperationUrl = "https://apis.roblox.com/cloud/v2/{}"
updateInstanceUrl = "https://apis.roblox.com/cloud/v2/universes/{}/places/{}/instances/{}"

# Load configuration
def load_config():
    with open(config_path, 'r') as config_file:
        return json.load(config_file)

# Ensure necessary directories exist
def ensure_directories():
    for dir_path in [lua_files_dir]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

# List children instances
def list_children(session, universeId, placeId, parent_id="root", numberOfRetries=10, retryPollingCadence=1):
    response = session.get(listChildrenUrl.format(universeId, placeId, parent_id), headers=headers)
    if response.status_code != 200:
        print("Failed to list instances:", response.text)
        return
    operationPath = response.json()['path']
    response = poll_for_results(session, operationPath)
    children = response['response']['instances']
    return children
        


# Get operation results
def get_operation(session, operationPath):
    url = getOperationUrl.format(operationPath)
    response = session.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

# Poll for operation results
def poll_for_results(session, operationPath, numberOfRetries=10, retryPollingCadence=5):
    for _ in range(numberOfRetries):
        time.sleep(retryPollingCadence)
        result = get_operation(session, operationPath)
        if result.get("done"):
            return result

# Update instance on Roblox
def update_instance(session, universeId, placeId, updateId, postData):
    url = updateInstanceUrl.format(universeId, placeId, updateId)
    response = session.patch(url, headers={**headers, **contentTypeHeader}, data=postData)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

# Generate post data for updating instances
def generate_post_data(type, source_code):
    return json.dumps({
        "engineInstance": {
            "Details": {type: {"Source": source_code}}
        }
    })

def list_and_create_scripts(session, universeId, placeId, instance_mapping, parent_id="root", parent_name="root", verion_control_name_whitelist=[]):
    children = list_children(session, universeId, placeId, parent_id)
    for child in children:
        is_container = child.get("hasChildren", False)
        instance = child.get("engineInstance", {})
        instance_details = instance.get("Details", {})
        instance_type_name, instance_type = next(((k, v) for k, v in instance_details.items() if k in ["Script", "LocalScript", "ModuleScript"]), (None, None))

        if instance_type:
            instance_id = instance.get("Id", "")
            instance_name = instance.get("Name", "")
            file_name = f"{parent_name}_{instance_name}-{instance_type_name}_{instance_id}.lua"
            file_path = os.path.join(lua_files_dir, file_name)
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(instance_type.get("Source", ""))
            print(f"Update {file_name} in {lua_files_dir}")
            instance_mapping[instance_id] = {
                "name": instance_name,
                "type": instance_type_name,
                "file_path": file_path
            }

        if is_container and (instance_type and instance_type.get("Folder") or instance.get("Name", "") in verion_control_name_whitelist):
            list_and_create_scripts(session, universeId, placeId, instance_mapping, parent_id=instance.get("Id", ""), parent_name=instance.get("Name", ""), verion_control_name_whitelist=verion_control_name_whitelist)

def update_all_instances(session, universeId, placeId, instance_mapping):
    for instance_id, details in instance_mapping.items():
        file_path = details.get("file_path")
        instance_type = details.get("type")
        with open(file_path, 'r', encoding='utf-8') as file:
            source_code = file.read()
        postData = generate_post_data(instance_type, source_code)
        result = update_instance(session, universeId, placeId, instance_id, postData)
        print(f"Updated {file_path} with result {result}")

def monitor_and_save_changes(session, universeId, placeId, instance_mapping, loop=True, timer=3):
    while True:
        for instance_id, details in instance_mapping.items():
            file_path = details.get("file_path")
            if os.path.getmtime(file_path) > details.get("last_modified", 0):
                with open(file_path, 'r', encoding='utf-8') as file:
                    source_code = file.read()
                postData = generate_post_data(details.get("type"), source_code)
                update_instance(session, universeId, placeId, instance_id, postData)
                details["last_modified"] = os.path.getmtime(file_path)
        if not loop:
            break
        time.sleep(timer)

def main():
    ensure_directories()
    session = requests.Session()
    config = load_config()
    universeId, placeId, verion_control_name_whitelist = config.get('universeId', ''), config.get('placeId', ''), config.get('verion_control_name_whitelist', [])
    instance_mapping = {}  # Load or initialize the instance mapping
    map_path="instance_mapping.json"
    # Check if the file exists
    if not os.path.exists(map_path):
        # If the file doesn't exist, create it and initialize with an empty dictionary
        with open(map_path, 'w') as f_out:
            json.dump({}, f_out)  # You can replace {} with your desired default content

    # Now that the file exists for sure, open it and load its content
    with open(map_path, 'r') as f_in:
        instance_mapping = json.load(f_in)
    # Argument parser setup
    parser = argparse.ArgumentParser(description="Roblox Lua Script Manager")
    parser.add_argument("-pull", help="Update the data model and .lua files", action="store_true")
    parser.add_argument("-push", help="Update the data model and .lua files", action="store_true")
    parser.add_argument("-monitor", help="Monitor changes and update .lua files as needed", action="store_true")
    args = parser.parse_args()    # Define arguments
    args = parser.parse_args()

    if args.pull:
        list_and_create_scripts(session, universeId, placeId, instance_mapping, verion_control_name_whitelist=verion_control_name_whitelist)
        # Save the instance_mapping to a file
    elif args.push:
        update_all_instances(session, universeId, placeId, instance_mapping)
    elif args.monitor:
        monitor_and_save_changes(session, universeId, placeId, instance_mapping, loop=True)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
