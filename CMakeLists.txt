# Sadly cannot use this with the newer pyproject.toml since 'uv pip install -e .' 
# executes this in a temporary python interpreter rather than the local .venv one.
cmake_minimum_required(VERSION 3.15)
project(streamyjson LANGUAGES CXX)

message(STATUS "🎯 Running CMake ...")

set(Python_FIND_VIRTUALENV FIRST) # This is the default.

#set(PYBIND11_CMAKE_DIR "/home/filip/coding/json_stream_parser/.venv/lib/python3.13/site-packages/pybind11/share/cmake/pybind11")
# The following command finds the pybind11 inside of the uv environment and sets (non-hardcoded version of set command above)
execute_process(
    COMMAND python -c "import pybind11; print(pybind11.get_cmake_dir())"
    OUTPUT_VARIABLE PYBIND11_CMAKE_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET
)
execute_process(
    COMMAND python -c "import site; print(site.getsitepackages()[0])"
    OUTPUT_VARIABLE PYTHON_SITE_PACKAGES
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
message(STATUS "The python env is: ${PYTHON_SITE_PACKAGES}")
message(STATUS "🎯 Done CMake for streamyjson...")
if(NOT PYBIND11_CMAKE_DIR)
    message(FATAL_ERROR "Could not find pybind11 CMake dir. Make sure you did uv add pybind11.")
else()
    message(STATUS "Found pybind11 CMake directory: ${PYBIND11_CMAKE_DIR}")
endif()

list(APPEND CMAKE_PREFIX_PATH ${PYBIND11_CMAKE_DIR})

# We have added the include path so now we can find the package
find_package(pybind11 REQUIRED)
# We found the package which contain this function
pybind11_add_module(cppjsonparser jsonparser.cpp)
