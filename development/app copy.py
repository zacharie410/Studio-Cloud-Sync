import requests
import json
import os
import time

# Provided API key and IDs
apiKey = "key_deleted"
universeId = "your_id"
placeId = "your_id"

# Headers and Endpoints
apiKeyHeaderKey = "x-api-key"

instanceId = "root"
headers = {apiKeyHeaderKey: apiKey}


listChildrenUrl = "https://apis.roblox.com/cloud/v2/universes/%s/places/%s/instances/%s:listChildren"
getOperationUrl = "https://apis.roblox.com/cloud/v2/%s"

numberOfRetries = 10
retryPollingCadence = 5

doneJSONKey = "done"

verion_control_name_whitelist = ["ServerScriptService", "StarterPlayer", "StarterGui"]

def ListChildren():
  url = listChildrenUrl % (universeId, placeId, instanceId)
  headerData = {apiKeyHeaderKey: apiKey}
  results = requests.get(url, headers = headerData)
  return results

def GetOperation(operationPath):
  url = getOperationUrl % (operationPath)
  headerData = {apiKeyHeaderKey: apiKey}
  results = requests.get(url, headers = headerData)
  return results

def PollForResults(operationPath):
  currentRetries = 0
  while (currentRetries < numberOfRetries):
    time.sleep(retryPollingCadence)
    results = GetOperation(operationPath)
    currentRetries += 1

    if (results.status_code != 200 or results.json()[doneJSONKey]):
      return results

# Directory to save .lua files
lua_files_dir = "roblox_lua_files"
if not os.path.exists(lua_files_dir):
    os.makedirs(lua_files_dir)

instance_mapping = {}

# Function to list script instances and create .lua files
def list_and_create_scripts(parent_id="root"):
    response = requests.get(listChildrenUrl % (universeId, placeId, parent_id), headers=headers)
    if response.status_code != 200:
        print("Failed to list instances:", response.text)
        return
    # Parse the Operation object's path to use in polling for the instance resource.
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
            file_name = f"{instance_name}_{instance_id}.lua"
            file_path = os.path.join(lua_files_dir, file_name)
            print(instance_type)
            # Write script content to file (for demo, writing instance name and type)
            with open(file_path, 'w', encoding='utf-8') as file:

                file_content = instance_type.get("Source")
                file.write(file_content)
            
            instance_mapping[instance_id] = {
                "name": instance_name,
                "type": instance_type_name,
                "file_path": file_path
            }

        if is_container and ( ((instance_type and instance_type.get("Folder")) or child["Name"] in verion_control_name_whitelist)):
           list_and_create_scripts(parent_id=child["Id"])

def update_datamodel():
    list_and_create_scripts()

    # Save instance mapping to a JSON file
    with open("instance_mapping.json", 'w', encoding='utf-8') as json_file:
        json.dump(instance_mapping, json_file, indent=4)

    print(f"Created {len(instance_mapping)} .lua files and updated mapping.")


# SECTION FOR UPDATING A SCRIPT
# JSON keys
detailsJSONKey = "Details"
updateInstanceUrl = "https://apis.roblox.com/cloud/v2/universes/%s/places/%s/instances/%s"
contentTypeHeaderKey = "Content-type"
contentTypeHeaderValue = "application/json"
engineInstanceJSONKey = "engineInstance"

def GeneratePostData(type, source_code):
  propertiesDict = {"Source": source_code}
  detailsDict = {type: propertiesDict}
  instanceDict = {detailsJSONKey: detailsDict}
  outerDict = {engineInstanceJSONKey: instanceDict}
  return json.dumps(outerDict)

def UpdateInstance(postData, updateId):
    url = updateInstanceUrl % (universeId, placeId, updateId)
    headerData = {apiKeyHeaderKey: apiKey,
    contentTypeHeaderKey: contentTypeHeaderValue}
    return requests.patch(url, headers = headerData, data = postData)

##END OF SECTION
# Poll for updates features SECTION
folder_path = 'roblox_lua_files'

# Function to get the current list of files and their last modification times
def get_current_files():
    try:
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        return {f: os.path.getmtime(os.path.join(folder_path, f)) for f in files}
    except Exception as e:
        print(f"Error accessing folder: {e}")
        return {}

def monitor_and_save_changes():
    # Initialize the tracking dictionary with the existing files and their modification times
    changes = get_current_files()

    while True:
        current_files = get_current_files()

        # Check for new or updated files
        for f, mtime in current_files.items():
            if f not in changes:
                print(f"New file detected: {f}")
                changes[f] = mtime
            elif changes[f] < mtime:
                print(f"File {f} has been modified")
                changes[f] = mtime

                with open(os.path.join(folder_path, f), 'r') as file:
                    data = file.read()
                    print("Attempting update")
                    id = f[-40:-4]
                    result = UpdateInstance(GeneratePostData(instance_mapping[id].get("type"), data), id)
                    print(f"Update result: {result}")

        # Optionally, check for deleted files
        for f in list(changes.keys()):
            if f not in current_files:
                print(f"File {f} was deleted or is no longer accessible")
                del changes[f]

        # Sleep for a specified interval before checking again
        time.sleep(3)

# Main function
def main():
    update_datamodel()
    monitor_and_save_changes()


if __name__ == "__main__":
    main()
