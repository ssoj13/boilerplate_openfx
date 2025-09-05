cmake_minimum_required(VERSION 3.14)
project(colorFill VERSION 1.0.0)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Include vcpkg toolchain file if not already set
if(NOT DEFINED CMAKE_TOOLCHAIN_FILE)
    set(CMAKE_TOOLCHAIN_FILE "$ENV{VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake"
        CACHE STRING "Vcpkg toolchain file")
endif()

# Find OpenFX package
find_package(unofficial-openfx CONFIG REQUIRED)

# Add source files
set(SOURCES
    src/colorFill.cpp
)

# Create shared library
add_library(colorFill SHARED ${SOURCES})

# Set output name and prefix
set_target_properties(colorFill PROPERTIES 
    PREFIX ""
    OUTPUT_NAME "colorFill.ofx"
)

# Link against OpenFX
target_link_libraries(colorFill PRIVATE unofficial::openfx::OpenFx)

# Include OpenFX headers
target_include_directories(colorFill PRIVATE 
    ${OpenFX_INCLUDE_DIRS}
    ${OpenFX_INCLUDE_DIRS}/Support
)

# Set installation directory
install(TARGETS colorFill
    LIBRARY DESTINATION ${CMAKE_INSTALL_PREFIX}/colorFill.ofx.bundle/Contents/${CMAKE_SYSTEM_NAME}-${CMAKE_SYSTEM_PROCESSOR}
)

# Copy the Info.plist file (you need to create this file)
install(FILES ${CMAKE_SOURCE_DIR}/Info.plist
    DESTINATION ${CMAKE_INSTALL_PREFIX}/colorFill.ofx.bundle/Contents
)
