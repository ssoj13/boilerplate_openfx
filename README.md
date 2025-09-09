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
- **Cross-Platform** - Windows/Linux/macOS support via CMake
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
- **Visual Studio 2019+** (Windows) or **GCC/Clang** (Linux/macOS)

### Build
```bash
# Clone and build
git clone <your-repo>
cd boilerplate_openfx

# Windows
build.cmd

# Linux/macOS
conan install . --output-folder=build --build=missing --settings=build_type=Release
cmake -S . -B build -DCMAKE_TOOLCHAIN_FILE=build/build/generators/conan_toolchain.cmake
cmake --build build --config Release
cmake --install build --config Release
```

## 🔧 Customizing for Your Plugin

1. **Update README badges** - Replace `YOUR_USERNAME/YOUR_REPO` with your GitHub details
2. **Rename** `colorFill.*` files to your plugin name
3. **Update** plugin identifier in `src/colorFill.cpp`:
   ```cpp
   static ColorFillPluginFactory p("com.yourcompany.YourPlugin", 1, 0);
   ```
4. **Modify** `CMakeLists.txt` project name and output
5. **Implement** your image processing logic in `render()` function
6. **Add parameters** in `describeInContext()`

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


