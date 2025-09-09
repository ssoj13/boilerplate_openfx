# OpenFX Plugin Boilerplate

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

1. **Rename** `colorFill.*` files to your plugin name
2. **Update** plugin identifier in `src/colorFill.cpp`:
   ```cpp
   static ColorFillPluginFactory p("com.yourcompany.YourPlugin", 1, 0);
   ```
3. **Modify** `CMakeLists.txt` project name and output
4. **Implement** your image processing logic in `render()` function
5. **Add parameters** in `describeInContext()`

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

## License

MIT


