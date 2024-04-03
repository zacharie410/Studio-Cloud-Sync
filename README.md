# Studio Cloud Sync: Simplifying Roblox Script Management

Studio Cloud Sync is a Python script designed to simplify the management of `.luau` files from Roblox Studio within your local environment using the Roblox Engine Open Cloud APIs. With Studio Cloud Sync, developers can seamlessly synchronize their local workspace with the cloud, enabling efficient version control and collaboration on Roblox experiences.

![Example Screenshot](/readme_images/example.png)

## Getting Started

### Prerequisites

- Python installed on your local machine.
- Roblox Studio installed.

### Setup

- **Clone Repository**: Ensure you have cloned the Studio Cloud Sync repository to your local machine.
- **API Key**: Obtain your API key from Roblox by following the instructions in the [Roblox documentation](https://create.roblox.com/docs/cloud/open-cloud/instance).

### Creating the `.env` File

1. In the root directory of your Studio Cloud Sync project, create a file named `.env`. This file will store your environment-specific settings, such as your API key, Roblox universe ID, and place ID.

2. Use the `.env.template` as a reference to add the necessary entries to your `.env` file:

   ```
   API_KEY="your_roblox_api_key_here"
   UNIVERSE_ID="your_universe_id_here"
   PLACE_ID="your_place_id_here"
   ```

   Replace the placeholder values with your actual Roblox API key, Universe ID, and Place ID.

### Preventing `.env` Leaks with `.gitignore`

Ensure your `.env` file is not accidentally committed to version control:

1. Open or create a `.gitignore` file in the root directory of your project.
2. Add `.env` to the `.gitignore` file to instruct Git to ignore it.

### Sharing `.env` Configurations Securely

1. **Create a Shared Configuration Template**: Copy your `.env` file, name it `.env.example` or `.env.template`, and remove or obfuscate any sensitive values.
2. **Use Secure Sharing Methods**: Share the template directly with colleagues through secure channels.

## Usage

Studio Cloud Sync can be used with the following command-line arguments:

```
python scs.py -pull     # Pull and update local .lua files
python scs.py -push     # Push local changes to the Roblox platform
python scs.py -monitor  # Monitor local changes and push updates automatically
```

## Features

- **Cloud-based Lua File Management**: Manage .lua files directly from Roblox Studio using the Roblox Engine Open Cloud APIs.
- **Local Workspace Integration**: Sync your local environment with the cloud for consistency and accessibility across platforms.
- **Version Control**: Track changes to your .lua files with a version history.
- **Automatic Synchronization**: Monitor local changes and automatically push updates to Roblox.

## Future Planned Features

- **CLI Distributable (.exe)**
- **UI App Version**
- **Full Multi-OS Support**

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

Thanks to the Roblox Engine Open Cloud APIs team and the Rojo team for their open-source contributions that inspire Studio Cloud Sync.