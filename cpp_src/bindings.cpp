
/**
 * Python bindings for the streaming JSON parser
 */

#include "jsonparser.h"
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

// macro defined in pybind11.h (common.h)
PYBIND11_MODULE(_core, m) {
    m.doc() = "C++ streaming JSON parser with Python bindings";

    // Expose the StreamJsonParser class along with its
    // constructor and two functions. 
    // Note that we use getPython for get to return a py::object
    py::class_<StreamingJsonParser>(m, "StreamingJsonParser")
        .def(py::init<bool>(), py::arg("strict_mode") = false)
        .def("consume", &StreamingJsonParser::consume)
        .def("get", &StreamingJsonParser::getPython);
            
    // Expose extra function for parsing without explictly creating obj. 
    m.def("parse_json", [](const std::string& json_str, bool strict_mode = false) {
            StreamingJsonParser parser(strict_mode);
            parser.consume(json_str);
            return parser.getPython();
        }, py::arg("json_str"), py::arg("strict_mode") = false);
}
