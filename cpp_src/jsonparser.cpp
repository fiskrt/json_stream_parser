/**
* StreamingJsonParser: A C++ implementation of a streaming JSON parser.
* With Python bindings using pybind11.
*/

#include "jsonparser.h"

#include <string>
#include <unordered_map>
#include <vector>
#include <memory>
#include <stdexcept>
#include <cassert>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;


// Default function parameter value is ONLY specified in header
StreamingJsonParser::StreamingJsonParser(bool strict_mode) 
    : state(START), strict_mode(strict_mode), result(std::make_unique<JsonObject>()) {
    // Initialize the expected characters for each state
    expected_chars[START] = "{";
    expected_chars[EXPECT_KEY_OR_END] = "\"}";
    expected_chars[EXPECT_COLON] = ":";
    expected_chars[EXPECT_VALUE] = "\"{";
    expected_chars[EXPECT_COMMA_OR_END] = ",}";
}

void StreamingJsonParser::consume(const std::string& buffer) {
    for (const char c : buffer) {
        if (isWhitespace(c) && state != IN_KEY && state != IN_VALUE) {
            continue;
        }
        
        if (strict_mode) {
            auto it = expected_chars.find(state);
            if (it != expected_chars.end() && it->second.find(c) == std::string::npos) {
                throw std::runtime_error(
                    "Got " + std::string(1, c) + " but expected one of " + it->second
                );
            }
        }
        
        processChar(c);
    }
}

bool StreamingJsonParser::isWhitespace(char c) const {
    return c == ' ' || c == '\n' || c == '\t' || c == '\r';
}

void StreamingJsonParser::processChar(char c) {
    JsonObject* current_obj = stack.empty() ? result.get() : stack.back();

    switch (state) {
        case START:
            if (c == '{') {
                state = EXPECT_KEY_OR_END;
            }
            break;
            
        case EXPECT_KEY_OR_END:
            if (c == '"') {
                state = IN_KEY;
                current_key = "";
            } else if (c == '}') {
                if (!stack.empty()) {
                    stack.pop_back();
                }
                state = EXPECT_COMMA_OR_END;
            }
            break;
            
        case IN_KEY:
            if (c == '"') {
                state = EXPECT_COLON;
            } else {
                current_key += c;
            }
            break;
            
        case IN_VALUE:
            if (c == '"') {
                state = EXPECT_COMMA_OR_END;
            } else {
                auto* value = current_obj->get(current_key);
                assert(value != nullptr && value->isString() && "current_obj not inited in IN_VALUE");
                // since value is a JsonValue*, must cast to JsonString*
                dynamic_cast<JsonString*>(value)->append(c);
            }
            break;
            
        case EXPECT_COLON:
            if (c == ':') {
                state = EXPECT_VALUE;
            }
            break;
            
        case EXPECT_VALUE:
            if (c == '"') {
                // we know it's a string value so set cur_obj[cur_key] = ""
                state = IN_VALUE;
                current_obj->set(current_key, std::make_unique<JsonString>());
            } else if (c == '{') {
                auto newObj = std::make_unique<JsonObject>();
                JsonObject* objPtr = newObj.get();
                // Transfer ownership of pointer to current_obj
                current_obj->set(current_key, std::move(newObj));
                // Store raw pointer (w/o ownership) on stack. current_obj has ownership
                // so we have to make sure that current_obj lives longer than the element
                // does on the stack:
                // This is satisifed because 1) current_obj points to result which is alive
                // the longest, or 2), points to the previous stack entry which by definition
                // of a stack will outlive it.
                stack.push_back(objPtr);
                state = EXPECT_KEY_OR_END;
            }
            break;
            
        case EXPECT_COMMA_OR_END:
            if (c == ',') {
                state = EXPECT_KEY_OR_END;
            } else if (c == '}') {
                if (!stack.empty()) {
                    stack.pop_back();
                }
                state = EXPECT_COMMA_OR_END;
            }
            break;
    }
}
