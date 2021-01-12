cmake_minimum_required (VERSION 3.8)

project ("path_engine")

if(WIN32)
    message("Building dll file on Windows")
elseif(UNIX)
    message("Building dylib file on ${CMAKE_SYSTEM_NAME}")
endif()

# note CMAKE_BUILD_TYPE WILL BE INGNORED for IDE generators, like Visual Studio and Xcode
# it only works for single-configuration generators, e.g., make and Ninja
# see https://cmake.org/cmake/help/v3.0/variable/CMAKE_BUILD_TYPE.html?highlight=cmake_build_types for details
set(CMAKE_BUILD_TYPE  "Release")
set(LIBRARY_OUTPUT_PATH  ${CMAKE_BINARY_DIR}/bin)

add_library(path_engine SHARED path_engine.cpp)