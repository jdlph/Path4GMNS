cmake_minimum_required(VERSION 3.15)
project(path4gmns)

set(VER "" CACHE STRING "specific version number")
set(INIT_FILE "${CMAKE_SOURCE_DIR}/${PROJECT_NAME}/__init__.py")

if (VER STREQUAL "")
    set(PIP_INSTALL python -m pip install ${PROJECT_NAME})
else()
    set(PIP_INSTALL python -m pip install ${PROJECT_NAME}==${VER})
endif()

function(get_version OUTPUT_VAR)
    file(READ "${INIT_FILE}" CONTENT)
    string(REGEX MATCH "__version__ = ['\"]([^'\"]*)['\"]" _ ${CONTENT})
    set(${OUTPUT_VAR} ${CMAKE_MATCH_1} PARENT_SCOPE)
endfunction()

get_version(LOCAL_VER)

add_custom_target(build
    COMMAND ${CMAKE_COMMAND} -E echo "-- building ${PROJECT_NAME}-${LOCAL_VER}..."
    COMMAND ${CMAKE_COMMAND} -E env python setup.py sdist bdist_wheel
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
)

add_custom_target(dev-install ALL
    COMMAND ${CMAKE_COMMAND} -E echo "-- development install: ${PROJECT_NAME}-${LOCAL_VER}..."
    COMMAND ${CMAKE_COMMAND} -E env python -m pip install -e ${CMAKE_SOURCE_DIR}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
)

add_custom_target(publish
    COMMAND ${CMAKE_COMMAND} -E echo "-- publish the package on PyPI: ${PROJECT_NAME}-${LOCAL_VER}..."
    COMMAND ${CMAKE_COMMAND} -E env python -m twine upload --repository pypi ${CMAKE_BINARY_DIR}/${PROJECT_NAME}-${LOCAL_VER}*
    DEPENDS build
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
)

add_custom_target(pypi-install
    COMMAND ${CMAKE_COMMAND} -E echo "-- PyPI install: ${PROJECT_NAME}..."
    COMMAND ${CMAKE_COMMAND} -E env python -m pip uninstall -y ${PROJECT_NAME}
    COMMAND ${CMAKE_COMMAND} -E env ${PIP_INSTALL}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
)

add_custom_target(reg-install
    COMMAND ${CMAKE_COMMAND} -E echo "-- regular install: ${PROJECT_NAME}-${LOCAL_VER}..."
    COMMAND ${CMAKE_COMMAND} -E env python -m pip uninstall -y ${PROJECT_NAME}
    COMMAND ${CMAKE_COMMAND} -E env python -m pip install ${CMAKE_SOURCE_DIR}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
)

add_custom_target(test
    COMMAND ${CMAKE_COMMAND} -E echo "-- conduct unit test: ${PROJECT_NAME}-${LOCAL_VER}..."
    COMMAND ${CMAKE_COMMAND} -E env python -m pytest
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
)

add_custom_target(test-coverage
    COMMAND ${CMAKE_COMMAND} -E echo "-- conduct unit test with coverage: ${PROJECT_NAME}-${LOCAL_VER}..."
    COMMAND ${CMAKE_COMMAND} -E env python -m pytest --cov=${PROJECT_NAME}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
)

add_custom_target(upgrade
    COMMAND ${CMAKE_COMMAND} -E echo "-- upgrade ${PROJECT_NAME} to the lastest from PyPI..."
    COMMAND ${CMAKE_COMMAND} -E env python -m pip install --upgrade ${PROJECT_NAME}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
)

add_custom_target(clean-cache
    COMMAND ${CMAKE_COMMAND} -E echo "-- cleaning up CMake temporary dir and files..."
    COMMAND ${CMAKE_COMMAND} -E remove_directory "${CMAKE_BINARY_DIR}/CMakeFiles"
    COMMAND ${CMAKE_COMMAND} -E remove "${CMAKE_BINARY_DIR}/CMakeCache.txt"
    COMMAND ${CMAKE_COMMAND} -E remove "${CMAKE_BINARY_DIR}/cmake_install.cmake"
    COMMAND ${CMAKE_COMMAND} -E remove "${CMAKE_BINARY_DIR}/MakeFile"
    COMMAND ${CMAKE_COMMAND} -E echo "-- clean complete."
)
