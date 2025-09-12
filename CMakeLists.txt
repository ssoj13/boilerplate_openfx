cmake_minimum_required(VERSION 3.15)
project(colorFill VERSION 1.0.0)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Find OpenFX package
find_package(openfx REQUIRED)

# Set custom plugin installation directory
if(NOT PLUGIN_INSTALLDIR)
  if(WIN32)
    set(PLUGIN_INSTALLDIR "C:/Program Files/Common Files/OFX/Plugins/Joss_examples")
  elseif(APPLE)
    set(PLUGIN_INSTALLDIR "/Library/OFX/Plugins/Joss_examples")
  elseif(UNIX)
    set(PLUGIN_INSTALLDIR "/usr/OFX/Plugins/Joss_examples")
  else()
    set(PLUGIN_INSTALLDIR "/unknown-os")
  endif()
endif()

# Set architecture directory
if(WIN32)
  set(ARCHDIR "Win64")
elseif(APPLE)
  set(ARCHDIR "MacOS")
elseif(UNIX)
  set(ARCHDIR "Linux-x86-64")
else()
  set(ARCHDIR "unknown-arch")
endif()

# Create shared library
add_library(colorFill SHARED src/colorFill.cpp)

# Set OpenFX plugin properties
set_target_properties(colorFill PROPERTIES 
    PREFIX ""
    SUFFIX ".ofx"
    C_VISIBILITY_PRESET hidden
    CXX_VISIBILITY_PRESET hidden
)

# Link against OpenFX
target_link_libraries(colorFill PRIVATE openfx::openfx)

# Configure and install Info.plist
set(PLUGIN_NAME colorFill)
set(PLUGIN_EXE colorFill.ofx)
set(BUNDLE_IDENTIFIER com.joss.colorFill)
set(PLUGIN_VERSION "1.0.0")

configure_file(${CMAKE_SOURCE_DIR}/Info.plist.in
               "${PLUGIN_INSTALLDIR}/colorFill.ofx.bundle/Contents/Info.plist")

# Install plugin binary to proper OFX bundle structure
install(TARGETS colorFill
    DESTINATION "${PLUGIN_INSTALLDIR}/colorFill.ofx.bundle/Contents/${ARCHDIR}"
)
