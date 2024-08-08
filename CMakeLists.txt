cmake_minimum_required(VERSION 3.8)
project(LocalPackageBuild)

set(PACKAGE_NAME path4gmns)
set(INIT_FILE "${CMAKE_SOURCE_DIR}/${PACKAGE_NAME}/__init__.py")

function(get_version OUTPUT_VAR)
    file(READ "${INIT_FILE}" CONTENT)
    string(REGEX MATCH "__version__ = ['\"]([^'\"]*)['\"]" _ ${CONTENT})
    set(${OUTPUT_VAR} ${CMAKE_MATCH_1} PARENT_SCOPE)
endfunction()

get_version(PACKAGE_VER)

add_custom_target(build ALL
    COMMAND ${CMAKE_COMMAND} -E echo "building ${PACKAGE_NAME}..."
    COMMAND ${CMAKE_COMMAND} -E env python setup.py sdist bdist_wheel
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}    
)

add_custom_target(install_package
    COMMAND ${CMAKE_COMMAND} -E echo "installing ${PACKAGE_NAME}-${PACKAGE_VER}..."
    COMMAND ${CMAKE_COMMAND} -E env python -m pip install ${CMAKE_SOURCE_DIR}/dist/${PACKAGE_NAME}-${PACKAGE_VER}-py3-none-any.whl
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
)

add_custom_target(force_install_package ALL
    COMMAND ${CMAKE_COMMAND} -E echo "installing ${PACKAGE_NAME}-${PACKAGE_VER}..."
    COMMAND ${CMAKE_COMMAND} -E env python -m pip install --force-reinstall ${CMAKE_SOURCE_DIR}/dist/${PACKAGE_NAME}-${PACKAGE_VER}-py3-none-any.whl
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
)

add_dependencies(install_package build)
add_dependencies(force_install_package build)