# OpenFX Plugin Boilerplate

<!-- Replace YOUR_USERNAME/YOUR_REPO with your actual GitHub repository -->
[![CI](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Conan](https://img.shields.io/badge/Conan-2.0+-blue.svg)](https://conan.io/)
[![OpenFX](https://img.shields.io/badge/OpenFX-1.4+-green.svg)](https://openeffects.org/)

A minimal, production-ready OpenFX plugin template using **Conan** for dependency management. Start building OpenFX plugins instantly without dealing with complex build setups.

## 🎯 What's Included

- **ColorFill Plugin** - Simple example that fills image with solid color
- **Modern C++** - Clean, well-structured code using OpenFX C++ Support Library
- **Conan Integration** - Automatic dependency management (no git submodules)
- **Windows Ready** - Optimized for Windows development with Visual Studio
- **Proper Bundle Structure** - Ready for DaVinci Resolve, Nuke, After Effects, etc.

## 📁 Project Structure

```
├── src/
│   ├── colorFill.h         # Plugin class declarations
│   └── colorFill.cpp       # Plugin implementation
├── CMakeLists.txt          # Build configuration
├── conanfile.py           # Dependencies (OpenFX, etc.)
├── build.cmd              # Windows build script
└── Info.plist            # OpenFX bundle metadata
```

## ⚡ Quick Start

### Prerequisites
- **CMake 3.15+**
- **Conan 2.0+** (`pip install conan`)
- **Visual Studio 2019+** (Windows)

## 🔨 Build

### Method 1: Simple Build Script (Recommended)
```cmd
# Clone the repository
git clone <your-repo>
cd boilerplate_openfx

# Run the build script - handles everything automatically
build.cmd
```

### Method 2: Manual Build Steps
```cmd
# Install dependencies
conan install . --output-folder=build --build=missing --settings=build_type=Release

# Configure CMake
cmake -S . -B build -G "Visual Studio 17 2022" -DCMAKE_TOOLCHAIN_FILE=build/generators/conan_toolchain.cmake -DCMAKE_BUILD_TYPE=Release

# Build the plugin
cmake --build build --config Release

# Install to system (optional)
cmake --install build --config Release
```

**Build Output:** `build/Release/colorFill.ofx.dll` - Your compiled OpenFX plugin!

## 📦 Installation

After building, install the plugin to your OpenFX host application:

### For Nuke
```cmd
# Copy to Nuke plugin directory
copy "build\Release\colorFill.ofx.dll" "C:\Program Files\Nuke15.1v1\plugins\"

# Or create bundle structure (recommended)
mkdir "C:\Program Files\Nuke15.1v1\plugins\colorFill.ofx.bundle\Contents\Win64\"
copy "build\Release\colorFill.ofx.dll" "C:\Program Files\Nuke15.1v1\plugins\colorFill.ofx.bundle\Contents\Win64\"
copy "Info.plist" "C:\Program Files\Nuke15.1v1\plugins\colorFill.ofx.bundle\Contents\"
```

### For DaVinci Resolve
```cmd
# Copy to Resolve OFX plugins directory
mkdir "%ProgramFiles%\Blackmagic Design\DaVinci Resolve\OFX\Plugins\colorFill.ofx.bundle\Contents\Win64\"
copy "build\Release\colorFill.ofx.dll" "%ProgramFiles%\Blackmagic Design\DaVinci Resolve\OFX\Plugins\colorFill.ofx.bundle\Contents\Win64\"
copy "Info.plist" "%ProgramFiles%\Blackmagic Design\DaVinci Resolve\OFX\Plugins\colorFill.ofx.bundle\Contents\"
```

### For After Effects (via OpenFX Bridge)
```cmd
# Copy to AE OpenFX plugins directory (requires OpenFX bridge plugin)
copy "build\Release\colorFill.ofx.dll" "C:\Program Files\Adobe\Adobe After Effects 2024\Support Files\Plug-ins\Effects\OpenFX\"
```

### Alternative: User Directory Installation
```cmd
# Install to user's OFX plugin directory (works for most hosts)
mkdir "%USERPROFILE%\AppData\Roaming\OFX\Plugins\colorFill.ofx.bundle\Contents\Win64\"
copy "build\Release\colorFill.ofx.dll" "%USERPROFILE%\AppData\Roaming\OFX\Plugins\colorFill.ofx.bundle\Contents\Win64\"
copy "Info.plist" "%USERPROFILE%\AppData\Roaming\OFX\Plugins\colorFill.ofx.bundle\Contents\"
```

## 🎬 Usage

### In Nuke
1. **Restart Nuke** after plugin installation
2. **Tab > Color > ColorFill** - Add the ColorFill node
3. **Set Color Parameter** - Adjust the RGBA color values
4. **Connect to your comp** - Use as a solid color source or overlay

```python
# Create ColorFill node via Python in Nuke
colorFill = nuke.createNode("ColorFill")
colorFill['color'].setValue([1.0, 0.0, 0.0, 1.0])  # Red color
```

### In DaVinci Resolve
1. **Restart Resolve** after plugin installation  
2. **Color Page > OpenFX > Custom > ColorFill** - Apply to a clip
3. **Inspector Panel** - Adjust color parameters
4. **Use for grades/effects** - Apply solid colors or blend modes

### In After Effects (with OpenFX Bridge)
1. **Install OpenFX Bridge plugin** first (AE doesn't support OFX natively)
2. **Effect > OpenFX > ColorFill** - Apply to layer
3. **Effect Controls** - Adjust color settings
4. **Keyframe colors** - Animate color changes over time

### Example Use Cases
- **Solid Color Backgrounds** - Generate colored backgrounds
- **Color Correction** - Use as reference colors
- **Compositing Helpers** - Color keys and mattes  
- **Test Patterns** - Color calibration and testing

## 🔧 Development Guide

### Customizing for Your Plugin

1. **Update README badges** - Replace `YOUR_USERNAME/YOUR_REPO` with your GitHub details
2. **Rename files** - Change `colorFill.*` to your plugin name
3. **Update plugin identifier** in `src/colorFill.cpp`:
   ```cpp
   static ColorFillPluginFactory p("com.yourcompany.YourPlugin", 1, 0);
   ```
4. **Modify CMakeLists.txt** - Update project name and output filename
5. **Implement image processing** - Add your algorithm in the `render()` function
6. **Add parameters** - Define controls in `describeInContext()`

### Key Files to Modify

**src/colorFill.cpp:**
- `describe()` - Plugin metadata (name, group, contexts, bit depths)
- `describeInContext()` - Parameters and clips definition  
- `render()` - Your image processing algorithm
- Plugin factory identifier for uniqueness

**CMakeLists.txt:**
- Project name and version
- Output .ofx filename  
- Installation paths

**Info.plist:**
- Bundle identifier and executable name
- Should match your .ofx filename

### Adding Parameters

```cpp
// In describeInContext() function
OFX::DoubleParamDescriptor *intensity = desc.defineDoubleParam("intensity");
intensity->setLabels("Intensity", "Intensity", "Effect intensity");
intensity->setDefault(1.0);
intensity->setRange(0.0, 2.0);

OFX::BooleanParamDescriptor *enable = desc.defineBooleanParam("enable");
enable->setLabels("Enable", "Enable", "Enable effect");
enable->setDefault(true);

OFX::ChoiceParamDescriptor *blendMode = desc.defineChoiceParam("blendMode");
blendMode->setLabels("Blend Mode", "Blend Mode", "Blending mode");
blendMode->appendOption("Normal");
blendMode->appendOption("Add");
blendMode->appendOption("Multiply");
```

### Image Processing Template

```cpp
void YourPlugin::render(const OFX::RenderArguments &args) {
    // Get input/output clips
    std::unique_ptr<OFX::Image> src(_srcClip->fetchImage(args.time));
    std::unique_ptr<OFX::Image> dst(_dstClip->fetchImage(args.time));
    
    // Get parameters at current time
    double intensity;
    _intensityParam->getValueAtTime(args.time, intensity);
    
    // Get render window and pixel data
    const auto renderWindow = args.renderWindow;
    auto* srcData = static_cast<float*>(src->getPixelData());
    auto* dstData = static_cast<float*>(dst->getPixelData());
    
    // Process pixels
    for (int y = renderWindow.y1; y < renderWindow.y2; ++y) {
        for (int x = renderWindow.x1; x < renderWindow.x2; ++x) {
            // Your image processing here
            // Access pixels: srcData[index], dstData[index]
        }
    }
}
```

### Troubleshooting

**Plugin not showing up in host application:**
- Check plugin is in correct directory for your host version
- Ensure proper bundle structure with `Contents/Win64/` folder
- Verify Info.plist matches plugin name exactly
- Restart host application completely

**Build errors:**
- Ensure Conan 2.0+ installed: `pip install --upgrade conan`
- Run `conan profile detect --force` to setup default profile  
- Check Visual Studio 2019+ installed with C++ workload
- Clear build directory: `rd /s /q build` then rebuild

**Plugin crashes host:**
- Check for null pointer access in render() function
- Verify all parameter fetches use correct types
- Enable debug builds: `--settings=build_type=Debug`
- Use debugger to attach to host process

**Missing parameters in UI:**
- Ensure parameters defined in `describeInContext()`
- Check parameter names don't conflict with OpenFX reserved words
- Verify correct context (Filter vs Generator) in `describe()`

## 🏗 Why This Template?

- **No Submodules** - Conan handles OpenFX dependency automatically  
- **Clean Build** - No vcpkg, no manual SDK setup
- **Modern Standards** - Uses OpenFX C++ wrappers, not raw C API
- **Bundle Ready** - Proper `.ofx.bundle` structure for all hosts
- **Minimal Setup** - Just clone and build

## 📦 Dependencies (via Conan)

- `openfx/[>=1.4.0]` - OpenFX API and Support Library
- `expat` - XML parsing (transitive)
- `opengl/system` - OpenGL headers (transitive)

## 🚀 Releases

Create releases by pushing git tags:
```bash
git tag v1.0.0
git push origin v1.0.0
```

This triggers automatic builds for Windows/Linux/macOS and creates a GitHub release with plugin binaries.

## 🔧 Status Badges Explained

- **CI Badge** - Shows if the latest build passed/failed
- **License Badge** - MIT license indicator  
- **Conan Badge** - Conan package manager version
- **OpenFX Badge** - OpenFX API compatibility

## License

MIT


