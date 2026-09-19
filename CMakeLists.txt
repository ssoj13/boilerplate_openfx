cmake_minimum_required(VERSION 3.23)

# version.txt is the single source of truth (also read by conanfile.py)
file(STRINGS "${CMAKE_CURRENT_SOURCE_DIR}/version.txt" SERIES_VERSION LIMIT_COUNT 1)
project(ofx_plugins VERSION ${SERIES_VERSION} LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# ---- Series metadata: edit here for your plugin series ----
set(OFX_PLUGIN_GROUPING  "Joss_examples")  # host menu group + default install subdir
set(OFX_BUNDLE_ID_PREFIX "com.joss")        # CFBundleIdentifier prefix (<prefix>.<plugin>)
option(OFX_BUILD_TEMPLATE_CHECK "Compile templates/plugin so the scaffold never rots" ON)

find_package(openfx REQUIRED)

# Default install prefix: system-wide OFX plugin directory.
# Override with: cmake --install build --prefix <dir>
if(CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)
  if(WIN32)
    set(CMAKE_INSTALL_PREFIX "C:/Program Files/Common Files/OFX/Plugins/${OFX_PLUGIN_GROUPING}" CACHE PATH "" FORCE)
  elseif(APPLE)
    set(CMAKE_INSTALL_PREFIX "/Library/OFX/Plugins/${OFX_PLUGIN_GROUPING}" CACHE PATH "" FORCE)
  else()
    set(CMAKE_INSTALL_PREFIX "/usr/OFX/Plugins/${OFX_PLUGIN_GROUPING}" CACHE PATH "" FORCE)
  endif()
endif()

include(cmake/OfxPlugin.cmake)
add_subdirectory(common)

# Every plugins/<name>/CMakeLists.txt is picked up automatically (`bootstrap.py new <Name>`)
file(GLOB plugin_lists CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/plugins/*/CMakeLists.txt")
foreach(plugin_list IN LISTS plugin_lists)
  get_filename_component(plugin_dir "${plugin_list}" DIRECTORY)
  add_subdirectory("${plugin_dir}")
endforeach()

# Instantiate templates/plugin exactly like `bootstrap.py new` does and build it (not installed)
if(OFX_BUILD_TEMPLATE_CHECK)
  set(PLUGIN_NAME  templateCheck)
  set(PLUGIN_CLASS TemplateCheck)
  set(PLUGIN_ID    "${OFX_BUNDLE_ID_PREFIX}.TemplateCheck")
  set(PLUGIN_LABEL "Template Check")
  set(template_out "${CMAKE_BINARY_DIR}/templateCheck")
  file(GLOB template_files CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/templates/plugin/*")
  foreach(template_file IN LISTS template_files)
    get_filename_component(file_name "${template_file}" NAME)
    string(REPLACE "@PLUGIN_NAME@" "${PLUGIN_NAME}" file_name "${file_name}")
    configure_file("${template_file}" "${template_out}/${file_name}" @ONLY)
  endforeach()
  set(OFX_PLUGIN_NO_INSTALL ON)
  add_subdirectory("${template_out}" "${CMAKE_BINARY_DIR}/templateCheck-build")
  unset(OFX_PLUGIN_NO_INSTALL)
endif()
