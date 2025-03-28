# 🚀 Streamy JSON Parser

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)

A lightning-fast, memory-efficient streaming JSON parser with zero dependencies.

`StreamingJsonParser` provides incremental parsing of JSON data, allowing you to process JSON as it arrives rather than waiting for the complete document. Perfect for handling large JSON responses from APIs, LLM outputs, and other streaming contexts.

## ✨ Features

- **🔄 True streaming** - Parse JSON as it arrives, character by character
- **📊 Partial results** - Access the current state of parsing at any point
- **🪶 Lightweight** - Zero dependencies, minimal memory footprint
- **⚡ Blazing fast** - O(n) time complexity
- **🔒 Optional strict mode** - Validate JSON syntax as you parse
- **🔍 Well-defined subset** - Focuses on objects and string values

## 📦 Installation
```bash
git clone https://github.com/fiskrt/json_stream_parser.git
```

## 🚀 Usage

### Basic Usage

```python
from json_parse import StreamingJsonParser

# Create a parser
parser = StreamingJsonParser()

# Feed it JSON data in chunks
parser.consume('{"user": "john_doe", "profile": {')
parser.consume('"age": "28", "location": "San Francisco"')

# Get the current state of the parsed JSON
result = parser.get()
print(result)
# {'user': 'john_doe', 'profile': {'age': '28', 'location': 'San Francisco'}}
```

### LLM Integration Example

```python
parser = StreamingJsonParser()

# Process streaming LLM response
for chunk in llm_streaming_response:
    parser.consume(chunk)
    # Access intermediate state if needed
    current_data = parser.get()
    update_ui(current_data)
```

### Strict Mode

```python
# Enable strict mode to validate JSON syntax
parser = StreamingJsonParser(strict_mode=True)

try:
    parser.consume('{"invalid":: "value"}')
except ValueError as e:
    print(f"Invalid JSON: {e}")
```

## 🔬 Technical Details

### Formal Grammar (BNF)

StreamingJsonParser implements a subset of JSON that handles objects and strings according to this grammar:

```
<json>         ::= <object>
<object>       ::= '{' <members> '}'
<members>      ::= ε | <member-list>
<member-list>  ::= <member> | <member> ',' <member-list>
<member>       ::= <string> ':' <value>
<value>        ::= <string> | <object>
<string>       ::= '"' <characters> '"'
<characters>   ::= ε | <character> <characters>
<character>    ::= any Unicode character except "
```

Whitespace is allowed:
```
<whitespace>   ::= ε | <ws-char> <whitespace>
<ws-char>      ::= ' ' | '\n' | '\t' | '\r'
```

### Complexity Analysis

- **Time Complexity**: O(n) where n is the length of the input
- **Space Complexity**: O(n)


## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.