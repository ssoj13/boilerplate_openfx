@echo off
cls
::rd /s /q build
mkdir build
cd build
::call "C:\Programs\Vs\22\VC\Auxiliary\Build\vcvars64.bat"
cmake ../ -G "Visual Studio 17 2022" "-DCMAKE_TOOLCHAIN_FILE=C:/Vcpkg/scripts/buildsystems/vcpkg.cmake" "-DVCPKG_TARGET_TRIPLET=x64-windows" "-DOFX_SDK_PATH=./openfx" && cmake --build . --target ALL_BUILD --config Release
:: --log-level ERROR
pause
cmake -P cmake_install.cmake

