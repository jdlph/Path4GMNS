cmake_minimum_required(VERSION 3.8)
project(LocalPackageBuild)

set(PACKAGE_NAME path4gmns)
set(VER "" CACHE STRING "specific version number")
set(INIT_FILE "${CMAKE_SOURCE_DIR}/${PACKAGE_NAME}/__init__.py")

if (VER STREQUAL "")
    set(PIP_INSTALL python -m pip install ${PACKAGE_NAME})
else()
    set(PIP_INSTALL python -m pip install ${PACKAGE_NAME}==${VER})
endif()

function(get_version OUTPUT_VAR)
    file(READ "${INIT_FILE}" CONTENT)
    string(REGEX MATCH "__version__ = ['\"]([^'\"]*)['\"]" _ ${CONTENT})
    set(${OUTPUT_VAR} ${CMAKE_MATCH_1} PARENT_SCOPE)
endfunction()

get_version(LOCAL_VER)

add_custom_target(build
    COMMAND ${CMAKE_COMMAND} -E echo "-- building ${PACKAGE_NAME}-${LOCAL_VER}..."
    COMMAND ${CMAKE_COMMAND} -E env python setup.py sdist bdist_wheel
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
)

add_custom_target(dev_install ALL
    COMMAND ${CMAKE_COMMAND} -E echo "-- development install: ${PACKAGE_NAME}-${LOCAL_VER}..."
    COMMAND ${CMAKE_COMMAND} -E env python -m pip install -e ${CMAKE_SOURCE_DIR}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
)

add_custom_target(pypi_install
    COMMAND ${CMAKE_COMMAND} -E echo "-- PyPI install: ${PACKAGE_NAME}..."
    COMMAND ${CMAKE_COMMAND} -E env ${PIP_INSTALL}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
)

add_custom_target(regular_install
    COMMAND ${CMAKE_COMMAND} -E echo "-- regular install: ${PACKAGE_NAME}-${LOCAL_VER}..."
    COMMAND ${CMAKE_COMMAND} -E env python -m pip install ${CMAKE_SOURCE_DIR}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
)

add_custom_target(upgrade
    COMMAND ${CMAKE_COMMAND} -E echo "-- upgrade ${PACKAGE_NAME} to the lastest from PyPI..."
    COMMAND ${CMAKE_COMMAND} -E env python -m pip install --upgrade ${PACKAGE_NAME}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
)

add_custom_target(full_clean
    COMMAND ${CMAKE_COMMAND} -E echo "-- cleaning up CMake temporary dir and files..."
    COMMAND ${CMAKE_COMMAND} -E remove_directory "${CMAKE_BINARY_DIR}/CMakeFiles"
    COMMAND ${CMAKE_COMMAND} -E remove "${CMAKE_BINARY_DIR}/CMakeCache.txt"
    COMMAND ${CMAKE_COMMAND} -E remove "${CMAKE_BINARY_DIR}/cmake_install.cmake"
    COMMAND ${CMAKE_COMMAND} -E remove "${CMAKE_BINARY_DIR}/MakeFile"
    COMMAND ${CMAKE_COMMAND} -E echo "-- clean complete."
)