# Studio Cloud Sync: Simplifying Roblox Script Management

Studio Cloud Sync is a Python script designed to simplify the management of .lua files from Roblox Studio within your local environment using the Roblox Engine Open Cloud APIs. With Studio Cloud Sync, developers can seamlessly synchronize their local workspace with the cloud, enabling efficient version control and collaboration on Roblox experiences.

## Getting Started

### Prerequisites

- Python installed on your local machine
- Roblox Studio installed

### Setup

1. **Clone Repository**: Clone the Studio Cloud Sync repository to your local machine.

2. **Configuration**: Create a `.env` file in the root directory and add your API key obtained from Roblox as per the instructions in the [Roblox documentation](https://create.roblox.com/docs/cloud/open-cloud/instance). Configure the `scs_config.json` file with your universe ID, place ID, and version control name whitelist. It should end up looking something like:
```json
{
  "universeId": "5830112232",
  "placeId": "1618917054",
  "version_control_name_whitelist": ["ServerScriptService", "StarterPlayer", "StarterGui"]
}

```
The `version_control_name_whitelist` in the `scs_config.json` file is a configuration option that allows you to specify a list of names of objects within Roblox Studio that you want to include in version control. This feature is necessary due to current beta restrictions imposed by the Roblox Engine Open Cloud APIs, which prevent the system from parsing a full workspace.

Explanation:

- **Version Control**: Version control is a system that records changes to files over time, allowing you to recall specific versions later. In the context of Roblox development, version control helps track changes made to scripts and other assets within a game or experience.

- **Name Whitelist**: The whitelist allows you to specify which objects you want to include in version control. Only the objects listed in the whitelist will be synchronized between your local environment and the Roblox cloud. This helps optimize synchronization and prevents unnecessary data transfer for objects that are not relevant to your current development tasks.

- **Beta Restrictions**: Due to the current beta restrictions imposed by the Roblox Engine Open Cloud APIs, the system cannot parse a full workspace. This means that Studio Cloud Sync cannot automatically synchronize all objects within your Roblox Studio workspace. Instead, you must explicitly specify the objects you want to include using the `version_control_name_whitelist`.

In the provided example configuration, the `version_control_name_whitelist` includes three objects: `"ServerScriptService"`, `"StarterPlayer"`, and `"StarterGui"`. These are commonly used objects in Roblox development and are likely to contain scripts and assets that you want to manage using Studio Cloud Sync.

To configure Studio Cloud Sync for your project, you should replace the placeholder values (`"5830112232"` for `universeId` and `"1618917054"` for `placeId`) with the actual IDs of your Roblox universe and starting place. Additionally, you can customize the `version_control_name_whitelist` by adding or removing object names as needed for your project.


## Usage

Once configured, you can use Studio Cloud Sync with the following command-line arguments:

```
python scs.py -pull     # Pull and update local .lua files
python scs.py -push     # Push local changes to the Roblox platform
python scs.py -monitor  # Monitor local changes and push updates automatically
```

## Features

- **Cloud-based Lua File Management**: Utilize the power of Roblox Engine Open Cloud APIs to manage .lua files directly from Roblox Studio.
  
- **Local Workspace Integration**: Sync your local environment with the cloud to ensure consistency and accessibility across different platforms.

- **Version Control**: Track changes to your .lua files and maintain a version history for easy rollback and collaboration.

- **Automatic Synchronization**: Monitor local changes and automatically push updates to the Roblox platform, streamlining your workflow.

## Future Planned Features

Studio Cloud Sync aims to continuously improve and expand its capabilities to better serve the needs of Roblox developers. Here are some future planned features:

## 1. CLI Distributable (.exe)

### Description:
- Develop a standalone executable version of Studio Cloud Sync that can be used directly from the command line interface (CLI).
- Ensure compatibility with the Windows operating system.
- Enable easy installation and usage without the need for Python or additional dependencies.

## 2. UI App Version

### Description:
- Create a user-friendly graphical user interface (GUI) application for Studio Cloud Sync.
- Provide intuitive features for configuring settings, managing .lua files, and monitoring synchronization.
- Enhance usability and accessibility for developers of all skill levels.

## 3. Full Multi-OS Support

### Description:
- Extend support for Studio Cloud Sync to multiple operating systems, including Windows, Linux, and macOS.
- Ensure seamless functionality across different platforms, maintaining consistency and reliability.
- Allow developers to use Studio Cloud Sync on their preferred operating system without limitations.

## Implementation Roadmap:

1. **Research and Planning**: Conduct thorough research on the requirements and best practices for developing CLI distributable and UI app versions. Define the scope and objectives for each feature.

2. **Development of CLI Distributable**: Utilize packaging tools and frameworks to create a standalone executable version of Studio Cloud Sync for Windows. Implement necessary features and ensure robustness and reliability.

3. **Development of UI App Version**: Design an intuitive and visually appealing user interface for Studio Cloud Sync. Implement functionality for configuration, file management, and synchronization. Conduct usability testing to gather feedback and iterate on design improvements.

4. **Testing and Quality Assurance**: Perform comprehensive testing on both the CLI distributable and UI app versions to identify and resolve any bugs or issues. Ensure compatibility and stability across different operating systems.

5. **Documentation and Release**: Prepare detailed documentation and guides for installing, configuring, and using the new features. Release the updated versions of Studio Cloud Sync to the developer community, providing support and assistance as needed.

## Contributing

Contributions are welcome! Please feel free to open issues or submit pull requests for any improvements or new features you'd like to see.

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

We extend our heartfelt appreciation to the dedicated team behind the Roblox Engine Open Cloud APIs. Their unwavering commitment to providing developers with robust and flexible tools has been instrumental in enabling the seamless integration of Studio Cloud Sync with Roblox Studio. 

We are also deeply grateful for the inspiration drawn from the open-source contributions of the Rojo team. Their innovative solutions have set a high standard in collaborative development within the Roblox community, inspiring projects like Studio Cloud Sync to push boundaries and elevate the developer experience.

With Studio Cloud Sync, managing Roblox scripts has never been more efficient. Join us in streamlining your development workflow and unlocking new possibilities in Roblox game creation!