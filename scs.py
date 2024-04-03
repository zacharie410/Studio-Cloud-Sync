import argparse
import json
import os
import requests
import time
from dotenv import load_dotenv
from typing import Dict, List

# Load environment and configurations
load_dotenv()
CONFIG_PATH = 'scs_config.json'
LUA_FILES_DIR = "ScriptExplorer"
MAP_PATH = "./scs_instance_map.json"
API_KEY = os.getenv('API_KEY', '')
HEADERS = {"x-api-key": API_KEY, "Content-type": "application/json"}

# API Endpoints
LIST_CHILDREN_URL = "https://apis.roblox.com/cloud/v2/universes/{}/places/{}/instances/{}:listChildren"
GET_OPERATION_URL = "https://apis.roblox.com/cloud/v2/{}"
UPDATE_INSTANCE_URL = "https://apis.roblox.com/cloud/v2/universes/{}/places/{}/instances/{}"

# Utility Functions
def load_config() -> Dict[str, any]:
    with open(CONFIG_PATH, 'r') as config_file:
        return json.load(config_file)

def ensure_directories() -> None:
    if not os.path.exists(LUA_FILES_DIR):
        os.makedirs(LUA_FILES_DIR)

def get_operation(session: requests.Session, operation_path: str) -> Dict[str, any]:
    url = GET_OPERATION_URL.format(operation_path)
    response = session.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def poll_for_results(session: requests.Session, operation_path: str, number_of_retries: int = 10, retry_polling_cadence: float = 0.2) -> Dict[str, any]:
    cadence_rate = retry_polling_cadence
    for _ in range(number_of_retries):
        time.sleep(cadence_rate)
        cadence_rate*=2 # basically the delay doubles at each try, so try a few in quick succession then wait longer
        result = get_operation(session, operation_path)
        if result.get("done"):
            return result
    raise TimeoutError("Polling for results timed out.")

def generate_post_data(instance_type: str, source_code: str) -> str:
    return json.dumps({
        "engineInstance": {
            "Details": {instance_type: {"Source": source_code}}
        }
    })

# Core Functions
def list_children(session: requests.Session, universe_id: str, place_id: str, parent_id: str = "root") -> List[Dict[str, any]]:
    response = session.get(LIST_CHILDREN_URL.format(universe_id, place_id, parent_id), headers=HEADERS)
    response.raise_for_status()
    operation_path = response.json()['path']
    result = poll_for_results(session, operation_path)
    return result['response']['instances']

def update_instance(session: requests.Session, universe_id: str, place_id: str, instance_id: str, post_data: str) -> Dict[str, any]:
    url = UPDATE_INSTANCE_URL.format(universe_id, place_id, instance_id)
    response = session.patch(url, headers=HEADERS, data=post_data)
    response.raise_for_status()
    return response.json()


def list_and_create_scripts(session, universeId, placeId, instance_mapping, parent_id="root", parent_name="root", version_control_name_whitelist=[]):
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
            file_path = os.path.join(LUA_FILES_DIR, file_name)
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(instance_type.get("Source", ""))
            print(f"Update {file_name} in {LUA_FILES_DIR}")
            instance_mapping[instance_id] = {
                "name": instance_name,
                "type": instance_type_name,
                "file_path": file_path
            }

        if is_container and (instance_type and instance_type.get("Folder") or instance.get("Name", "") in version_control_name_whitelist):
            list_and_create_scripts(session, universeId, placeId, instance_mapping, parent_id=instance.get("Id", ""), parent_name=instance.get("Name", ""), version_control_name_whitelist=version_control_name_whitelist)

def save_instance_mapping(instance_mapping: Dict[str, Dict[str, str]]) -> None:
    with open(MAP_PATH, 'w') as file:
        json.dump(instance_mapping, file)

def update_all_instances(session: requests.Session, universe_id: str, place_id: str, instance_mapping: Dict[str, Dict[str, str]]) -> None:
    for instance_id, details in instance_mapping.items():
        file_path = details['file_path']
        instance_type = details['type']
        with open(file_path, 'r', encoding='utf-8') as file:
            source_code = file.read()
        post_data = generate_post_data(instance_type, source_code)
        result = update_instance(session, universe_id, place_id, instance_id, post_data)
        print(f"Updated {file_path} with result {result}")

def monitor_and_save_changes(session: requests.Session, universe_id: str, place_id: str, instance_mapping: Dict[str, Dict[str, any]], 
                             loop: bool = True, timer: int = 3) -> None:
    try:
        print("Monitoring changes... Press CTRL+C to exit.")
        while True:
            for instance_id, details in instance_mapping.items():
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
    ensure_directories()
    session = requests.Session()
    config = load_config()
    universe_id, place_id = config.get('universeId', ''), config.get('placeId', '')
    version_control_name_whitelist = config.get('version_control_name_whitelist', [])
    instance_mapping = {}

    if os.path.exists(MAP_PATH):
        with open(MAP_PATH, 'r') as file:
            instance_mapping = json.load(file)

    parser = argparse.ArgumentParser(description="Roblox Lua Script Manager")
    parser.add_argument("-pull", help="Pull and update the local .lua files", action="store_true")
    parser.add_argument("-push", help="Push local changes to the Roblox platform", action="store_true")
    parser.add_argument("-monitor", help="Monitor local changes and push updates automatically", action="store_true")
    args = parser.parse_args()

    if args.pull:
        list_and_create_scripts(session, universe_id, place_id, instance_mapping, version_control_name_whitelist=version_control_name_whitelist)
        save_instance_mapping(instance_mapping)
    elif args.push:
        update_all_instances(session, universe_id, place_id, instance_mapping)
    elif args.monitor:
        monitor_and_save_changes(session, universe_id, place_id, instance_mapping, loop=True)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
