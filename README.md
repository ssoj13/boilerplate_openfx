# OpenFX Plugin Boilerplate

[![CI](https://github.com/ssoj13/boilerplate_openfx/actions/workflows/ci.yml/badge.svg)](https://github.com/ssoj13/boilerplate_openfx/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Conan](https://img.shields.io/badge/Conan-2.0+-blue.svg)](https://conan.io/)
[![OpenFX](https://img.shields.io/badge/OpenFX-1.4+-green.svg)](https://openeffects.org/)

Minimal OpenFX plugin template with Conan. No complex dependency management, just clone and build.
Add your logic and get your plug-in ready in no time.


![DaVinci Resolve Plugin](docs/davinci20.png)


**What you get:**
- ColorFill example plugin (fills image with solid color)
- C++14 with OpenFX C++ wrappers (no raw C API)
- Conan handles OpenFX SDK (no git submodules)
- Windows/CMakelists focused
- Proper .ofx bundle structure for hosts

## 📁 Project Structure

```
├── src/
│   ├── colorFill.h         # Plugin class declarations
│   └── colorFill.cpp       # Plugin implementation
├── CMakeLists.txt          # Build configuration
├── conanfile.py           # Dependencies (OpenFX, etc.)
├── build.cmd              # Windows build script  
└── Info.plist.in          # OpenFX bundle template
```

## Build

**Prerequisites:** CMake 3.15+, Conan 2.0+, Visual Studio 2019+

**Just run:** `build.cmd`

Or manually:
```cmd
conan install . --output-folder=build --build=missing --settings=build_type=Release
cmake -S . -B build -G "Visual Studio 17 2022" -DCMAKE_TOOLCHAIN_FILE="build/generators/conan_toolchain.cmake"
cmake --build build --config Release
```

Output: `build/Release/colorFill.ofx`

## Installation  

**Auto-install:** Run `cmake --install build --config Release`  
Installs to: `C:\Program Files\Common Files\OFX\Plugins\Joss_examples\colorFill.ofx.bundle\`

**Manual install:** Copy `.ofx` file to:
- **Nuke:** `C:\Program Files\Nuke##\plugins\`  
- **Resolve:** `C:\Program Files\Blackmagic Design\DaVinci Resolve\OFX\Plugins\`  
- **User:** `%USERPROFILE%\AppData\Roaming\OFX\Plugins\`

## Usage

Restart your host app. Find ColorFill under Color or Custom effects.

**Nuke Python:**
```python
colorFill = nuke.createNode("ColorFill")
colorFill['color'].setValue([1.0, 0.0, 0.0, 1.0])
```

## Development

**To make your own plugin:**

1. Rename `colorFill.*` files to `yourPlugin.*`
2. Update plugin ID: `static YourPluginFactory p("com.yourcompany.YourPlugin", 1, 0);`
3. Change CMakeLists.txt project name and output filename
4. Write your image processing in `render()` function
5. Add UI controls in `describeInContext()`

**Key functions:**
- `describe()` - Plugin metadata, supported formats
- `describeInContext()` - Define parameters and clips
- `render()` - Process pixels here

**Parameter examples:**
```cpp
// Slider
auto intensity = desc.defineDoubleParam("intensity");
intensity->setRange(0.0, 2.0);
intensity->setDefault(1.0);

// Checkbox  
auto enable = desc.defineBooleanParam("enable");
enable->setDefault(true);

// Dropdown
auto mode = desc.defineChoiceParam("mode");
mode->appendOption("Normal");
mode->appendOption("Add");
```

**Render function skeleton:**
```cpp
void YourPlugin::render(const OFX::RenderArguments &args) {
    auto src = std::unique_ptr<OFX::Image>(_srcClip->fetchImage(args.time));
    auto dst = std::unique_ptr<OFX::Image>(_dstClip->fetchImage(args.time));
    
    double intensity;
    _intensityParam->getValueAtTime(args.time, intensity);
    
    // Process pixels in args.renderWindow
    // float* srcData = static_cast<float*>(src->getPixelData());
    // float* dstData = static_cast<float*>(dst->getPixelData());
}
```

## Troubleshooting

**Plugin missing:** Wrong directory, bundle structure, or host needs restart  
**Build fails:** Update Conan, check VS2019+, clear build folder  
**Crashes:** Null pointers, wrong parameter types  
**No parameters:** Check `describeInContext()` function

## Github Actions and Releases

Push tags to trigger Windows builds:
```bash
git tag v1.0.0 && git push origin v1.0.0
```

## License

MIT

## Acknowledgements

Special thanks to [Claude Code](https://www.anthropic.com/claude-code) and [Qwen Code](https://github.com/QwenLM/qwen-code) for simplifying boring tasks and tremendous help with development.
