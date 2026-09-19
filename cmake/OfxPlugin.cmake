# add_ofx_plugin_bundle(<name>
#     ID <ofx.plugin.identifier>      # required; keep stable once shipped (hosts store it in projects)
#     SOURCES <files...>              # required
#     [LABEL <ui label>]              # default: <name>
#     [BUNDLE_ID <reverse.dns.id>]    # default: ${OFX_BUNDLE_ID_PREFIX}.<name>
#     [VERSION <major.minor[.patch]>] # default: ${PROJECT_VERSION} (version.txt)
# )
#
# Builds <name>.ofx and installs <prefix>/<name>.ofx.bundle/Contents/{Info.plist,<arch>/<name>.ofx}
# as install COMPONENT <name>. Set OFX_PLUGIN_NO_INSTALL in the calling scope to build only.
#
# Not using add_ofx_plugin() from the Conan-provided OpenFX.cmake build module: it hardcodes
# ${CMAKE_SOURCE_DIR}/Examples/Info.plist.in and writes the plist into the install dir at configure time.

# Bundle architecture dir, per OFX spec (openfx Documentation/sources/Reference/ofxPackaging.rst)
if(WIN32)
  if(CMAKE_CXX_COMPILER_ARCHITECTURE_ID MATCHES "ARM64")
    set(OFX_ARCHDIR "Win-arm64")
  else()
    set(OFX_ARCHDIR "Win64")
  endif()
elseif(APPLE)
  set(OFX_ARCHDIR "MacOS")  # universal binaries, no per-arch dir
elseif(CMAKE_SYSTEM_PROCESSOR STREQUAL "x86_64")
  set(OFX_ARCHDIR "Linux-x86-64")
else()
  set(OFX_ARCHDIR "Linux-${CMAKE_SYSTEM_PROCESSOR}")  # Linux-$(uname -m), e.g. Linux-aarch64
endif()

set(OFX_PLUGIN_PLIST_TEMPLATE "${CMAKE_CURRENT_LIST_DIR}/Info.plist.in")

function(add_ofx_plugin_bundle NAME)
  cmake_parse_arguments(PARSE_ARGV 1 ARG "" "ID;LABEL;BUNDLE_ID;VERSION" "SOURCES")
  if(NOT ARG_ID)
    message(FATAL_ERROR "add_ofx_plugin_bundle(${NAME}): ID is required")
  endif()
  if(NOT ARG_SOURCES)
    message(FATAL_ERROR "add_ofx_plugin_bundle(${NAME}): SOURCES is required")
  endif()
  if(NOT ARG_LABEL)
    set(ARG_LABEL "${NAME}")
  endif()
  if(NOT ARG_BUNDLE_ID)
    set(ARG_BUNDLE_ID "${OFX_BUNDLE_ID_PREFIX}.${NAME}")
  endif()
  if(NOT ARG_VERSION)
    set(ARG_VERSION "${PROJECT_VERSION}")
  endif()
  string(REPLACE "." ";" version_parts "${ARG_VERSION}")
  list(GET version_parts 0 version_major)
  list(LENGTH version_parts version_len)
  if(version_len GREATER 1)
    list(GET version_parts 1 version_minor)
  else()
    set(version_minor 0)
  endif()

  # MODULE: loaded at runtime via LoadLibrary/dlopen, never linked against (no import lib)
  add_library(${NAME} MODULE ${ARG_SOURCES})
  set_target_properties(${NAME} PROPERTIES
    PREFIX ""
    SUFFIX ".ofx"
    CXX_VISIBILITY_PRESET hidden
    VISIBILITY_INLINES_HIDDEN ON
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
  )
  target_compile_definitions(${NAME} PRIVATE
    PLUGIN_ID="${ARG_ID}"
    PLUGIN_LABEL="${ARG_LABEL}"
    PLUGIN_GROUPING="${OFX_PLUGIN_GROUPING}"
    PLUGIN_VERSION_MAJOR=${version_major}
    PLUGIN_VERSION_MINOR=${version_minor}
  )
  target_link_libraries(${NAME} PRIVATE ofx_common)

  # Info.plist variables (function scope)
  set(PLUGIN_NAME ${NAME})
  set(PLUGIN_EXE ${NAME}.ofx)
  set(BUNDLE_IDENTIFIER ${ARG_BUNDLE_ID})
  set(PLUGIN_VERSION ${ARG_VERSION})
  configure_file(${OFX_PLUGIN_PLIST_TEMPLATE} ${CMAKE_CURRENT_BINARY_DIR}/Info.plist)

  if(NOT OFX_PLUGIN_NO_INSTALL)
    set(bundle_dir "${NAME}.ofx.bundle/Contents")
    install(TARGETS ${NAME} LIBRARY DESTINATION "${bundle_dir}/${OFX_ARCHDIR}" COMPONENT ${NAME})
    install(FILES ${CMAKE_CURRENT_BINARY_DIR}/Info.plist DESTINATION "${bundle_dir}" COMPONENT ${NAME})
  endif()
endfunction()
