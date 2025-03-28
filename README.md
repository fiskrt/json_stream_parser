# 🚀 Streamy JSON Parser

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)

A lightning-fast, stach-based, memory-efficient streaming JSON parser with zero dependencies.

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
import os
import asyncio
from openai import AsyncOpenAI
from streaming_json_parser import StreamingJsonParser

async def stream_json_from_openai():
    client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    parser = StreamingJsonParser()
    
    # Request that explicitly asks for JSON output
    stream = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Return JSON responses only."},
            {"role": "user", "content": "Give me a user profile with name, age, and interests."}
        ],
        response_format={"type": "json_object"},
        stream=True
    )
    
    # Process the streaming response
    async for chunk in stream:
        if chunk.choices[0].delta.content:
            text_chunk = chunk.choices[0].delta.content
            parser.consume(text_chunk)
            current_json = parser.get()
            
            if "name" in current_json:
                print(f"Name received: {current_json['name']}")
            
            if "interests" in current_json:
                print(f"Interests so far: {len(current_json['interests'])}")
    
    return parser.get()

if __name__ == "__main__":
    result = asyncio.run(stream_json_from_openai())
    print(f"Complete profile: {result}")
```

### Strict Mode

```python
# Enable strict mode to validate JSON syntax
parser = StreamingJsonParser(strict_mode=True)

try:
    parser.consume('{"invalid"a: "value"}')
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

## Credits
Claude 3.7 Sonnet (extended thinking)