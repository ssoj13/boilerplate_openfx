# Header-only helpers shared by all plugins (see include/ofxc/ofxc.h)
add_library(ofx_common INTERFACE)
target_include_directories(ofx_common INTERFACE ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_link_libraries(ofx_common INTERFACE openfx::Support)
