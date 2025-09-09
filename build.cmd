@echo off
cls

echo Installing Conan dependencies...
conan install . --output-folder=build --build=missing --settings=build_type=Release

echo Configuring CMake with Conan toolchain...
cmake -S . -B build -G "Visual Studio 17 2022" -DCMAKE_TOOLCHAIN_FILE="build/generators/conan_toolchain.cmake" -DCMAKE_BUILD_TYPE=Release

echo Building project...
cmake --build build --config Release

echo Installing plugin...
cmake --install build --config Release

echo Build complete!
pause

