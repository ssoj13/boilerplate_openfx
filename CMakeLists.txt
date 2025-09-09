cmake_minimum_required(VERSION 3.15)
project(colorFill VERSION 1.0.0)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Find OpenFX package
find_package(openfx REQUIRED)

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
target_link_libraries(colorFill PRIVATE openfx::openfx)

# Set installation directory
install(TARGETS colorFill
    LIBRARY DESTINATION ${CMAKE_INSTALL_PREFIX}/colorFill.ofx.bundle/Contents/${CMAKE_SYSTEM_NAME}-${CMAKE_SYSTEM_PROCESSOR}
)

# Copy the Info.plist file (you need to create this file)
install(FILES ${CMAKE_SOURCE_DIR}/Info.plist
    DESTINATION ${CMAKE_INSTALL_PREFIX}/colorFill.ofx.bundle/Contents
)
