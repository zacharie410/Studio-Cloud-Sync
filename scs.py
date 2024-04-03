import argparse
import json
import os
import requests
import time
from dotenv import load_dotenv
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import re

# Load environment and configurations
load_dotenv()
LUA_FILES_DIR = "ScriptExplorer"
API_KEY = os.getenv('API_KEY', '')
HEADERS = {"x-api-key": API_KEY, "Content-type": "application/json"}

# API Endpoints
LIST_CHILDREN_URL = "https://apis.roblox.com/cloud/v2/universes/{}/places/{}/instances/{}:listChildren"
GET_OPERATION_URL = "https://apis.roblox.com/cloud/v2/{}"
UPDATE_INSTANCE_URL = "https://apis.roblox.com/cloud/v2/universes/{}/places/{}/instances/{}"

# Define markers for the metadata section
METADATA_START_MARKER = "--[[METADATA"
METADATA_END_MARKER = "METADATA]]--"

# Utility Functions
def ensure_directories() -> None:
    if not os.path.exists(LUA_FILES_DIR):
        os.makedirs(LUA_FILES_DIR)

def get_operation(session: requests.Session, operation_path: str) -> Dict[str, Any]:
    url = GET_OPERATION_URL.format(operation_path)

    response = session.get(url, headers=HEADERS, timeout=1)
    code = response.status_code
    if code == 429:
        print("Too many requests, sleeping for 15 seconds")
        time.sleep(15)
        session = requests.Session()
        return get_operation(session, operation_path)
    response.raise_for_status()
    return response.json()

def poll_for_results(session: requests.Session, operation_path: str, number_of_retries: int = 3, retry_polling_cadence: float = 5) -> Dict[str, Any]:
    time.sleep(5)
    cadence_rate = retry_polling_cadence
    for _ in range(number_of_retries):
        result = get_operation(session, operation_path)
        if result.get("done"):
            return result
        time.sleep(cadence_rate)
        cadence_rate*=2 # basically the delay doubles at each try, so try a few in quick succession then wait longer

    raise TimeoutError("Polling for results timed out.")

def generate_post_data(instance_type: str, source_code: str) -> str:
    return json.dumps({
        "engineInstance": {
            "Details": {instance_type: {"Source": source_code}}
        }
    })

# Core Functions
def list_children(session: requests.Session, universe_id: str, place_id: str, parent_id: str = "root") -> List[Dict[str, Any]]:
    response = session.get(LIST_CHILDREN_URL.format(universe_id, place_id, parent_id), headers=HEADERS, timeout=1)
    code = response.status_code
    if code == 429:
        print("Too many requests, sleeping for 15 seconds")
        time.sleep(15)
        session = requests.Session()
        return list_children(session, universe_id, place_id, parent_id)
    response.raise_for_status()
    operation_path = response.json()['path']
    result = poll_for_results(session, operation_path)
    return result['response']['instances']

def update_instance(session: requests.Session, universe_id: str, place_id: str, instance_id: str, post_data: str, number_of_retries: int = 3, retry_polling_cadence: float = 0.2) -> Dict[str, Any]:
        cadence_rate = retry_polling_cadence
        url = UPDATE_INSTANCE_URL.format(universe_id, place_id, instance_id)
        for _ in range(number_of_retries):
            time.sleep(cadence_rate)
            cadence_rate*=2
            try:

                response = session.patch(url, headers=HEADERS, data=post_data)
                response.raise_for_status()
                return response.json()
            except:
                print("Save failed, trying again . . .")


def extract_metadata(file_path: str) -> str:
    
    # Compile a regular expression to find the instanceId line
    instance_id_pattern = re.compile(r'\binstanceId:\s*(\S+)')
    # Compile a regular expression to find the instanceType line
    instance_type_pattern = re.compile(r'\binstanceType:\s*(\S+)')

    # Initialize variables
    instance_id = None
    instance_type = None
    # Read the file content
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Find the metadata section
    metadata_start_index = content.find(METADATA_START_MARKER)
    metadata_end_index = content.find(METADATA_END_MARKER, metadata_start_index)
    
    if metadata_start_index != -1 and metadata_end_index != -1:
        # Extract the metadata section
        metadata_section = content[metadata_start_index:metadata_end_index + len(METADATA_END_MARKER)]
        
        # Search for the instanceId within the metadata section
        match = instance_id_pattern.search(metadata_section)
        if match:
            instance_id = match.group(1)  # The first capturing group contains the instanceId
         # Search for the instanceType within the metadata section
        match = instance_type_pattern.search(metadata_section)
        if match:
            instance_type = match.group(1)  # The first capturing group contains the instanceId
    
    return instance_id, instance_type

def update_metadata(file_path:str, instance_id: str, instance_type: str) -> str:
    # Format the new metadata section

    new_metadata = f"""{METADATA_START_MARKER}
        instanceId: {instance_id}
        instanceType: {instance_type}
        {METADATA_END_MARKER}
    """
    # Read the existing file content
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Split the content at the metadata section
    parts = content.split(METADATA_START_MARKER, 1)
    pre_metadata = parts[0]
    post_metadata = parts[1].split(METADATA_END_MARKER, 1)[1] if len(parts) > 1 else ""

    # Combine the new metadata with the main content
    updated_content = pre_metadata + new_metadata + post_metadata

    # Write the updated content back to the file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(updated_content)

def list_and_create_scripts(session, universeId, placeId, parent_id="root", parent_name="root"):
    try:
        children = list_children(session, universeId, placeId, parent_id)
        tasks = []
        for child in children:
            is_container = child.get("hasChildren", False)
            instance = child.get("engineInstance", {})
            instance_details = instance.get("Details", {})
            instance_type_name, instance_type = next(((k, v) for k, v in instance_details.items() if k in ["Script", "LocalScript", "ModuleScript"]), (None, None))
            if instance_type:
                instance_id = instance.get("Id", "")
                instance_name = instance.get("Name", "")
                file_name = f"{parent_name}_{instance_name}-{instance_type_name}.luau"
                file_path = os.path.join(LUA_FILES_DIR, file_name)

                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(instance_type.get("Source", ""))

                update_metadata(file_path, instance_id, instance_type_name)

                print(f"Pulled {file_name} in {LUA_FILES_DIR}")

            if is_container:
                tasks.append(partial(list_and_create_scripts, session, universeId, placeId,
                         parent_id=instance.get("Id", ""),
                         parent_name=instance.get("Name", ""),
                         ))

        with ThreadPoolExecutor() as executor:
            for task_with_args in tasks:
                executor.submit(task_with_args)
    except Exception as e:
        print(e)

def update_all_instances(session: requests.Session, universe_id: str, place_id: str) -> None:
        files = [f for f in os.listdir(LUA_FILES_DIR) if os.path.isfile(os.path.join(LUA_FILES_DIR, f))]
        for file in files:
            file_path = os.path.join(LUA_FILES_DIR, file)
            with open(file_path, 'r', encoding='utf-8') as file:
                source_code = file.read()
            file_id, file_type = extract_metadata(file_path)
            post_data = generate_post_data(file_type, source_code)
            print(post_data)
            result = update_instance(session, universe_id, place_id, file_id, post_data)
            print(f"Updated {file_path} with result {result}")

def monitor_and_save_changes(session: requests.Session, universe_id: str, place_id: str, 
                             loop: bool = True, timer: int = 3) -> None:
    try:
        print("Monitoring changes... Press CTRL+C to exit.")
        while True:
            for instance_id, details in {}.items():
                file_path = details['file_path']
                if os.path.getmtime(file_path) > details.get('last_modified', 0):
                    with open(file_path, 'r', encoding='utf-8') as file:
                        source_code = file.read()
                    post_data = generate_post_data(details['type'], source_code)
                    result = update_instance(session, universe_id, place_id, instance_id, post_data)
                    details['last_modified'] = os.path.getmtime(file_path)
                    print(f"Change detected. Updated {file_path} with result {result}")
            if not loop:
                break
            time.sleep(timer)
    except KeyboardInterrupt:
        print("Monitoring interrupted by user. Exiting...")

# Main Function
def main() -> None:
    parser = argparse.ArgumentParser(description="Roblox Lua Script Manager")
    parser.add_argument("-pull", help="Pull and update the local .lua files", action="store_true")
    parser.add_argument("-push", help="Push local changes to the Roblox platform", action="store_true")
    parser.add_argument("-monitor", help="Monitor local changes and push updates automatically", action="store_true")
    parser.add_argument("-init", help="Setup the local file environment at the specified directory path", action="store_true")

    args = parser.parse_args()

    if args.init:
        ensure_directories()
        return
    
    session = requests.Session()
    universe_id, place_id = os.getenv('UNIVERSE_ID', ''), os.getenv('PLACE_ID', '')

    if args.pull:
        
        list_and_create_scripts(session, universe_id, place_id)
    elif args.push:

        update_all_instances(session, universe_id, place_id)
    elif args.monitor:

        monitor_and_save_changes(session, universe_id, place_id, loop=True)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()