# colorFill OpenFX Plugin

This is a simple OpenFX plugin that fills the output with a single color. It's designed to work with Nuke and other OpenFX-compatible applications.

## Requirements

- OpenFX SDK
- CMake 3.12 or higher
- C++11 compatible compiler

## Building

1. Clone this repository
2. Set the `OFX_SDK_PATH` in CMakeLists.txt to point to your OpenFX SDK installation
3. Create a build directory:
   ```
   mkdir build
   cd build
   ```
4. Run CMake:
   ```
   cmake ..
   ```
5. Build the project:
   ```
   make
   ```
6. Install the plugin:
   ```
   make install
   ```

## Usage

After installation, the plugin should be available in Nuke as "ColorFill". It provides a single color parameter that can be animated.

## License


