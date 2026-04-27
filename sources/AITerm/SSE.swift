//
//  SSE.swift
//  iTerm2
//
//  Created by George Nachman on 6/6/25.
//

func SplitServerSentEvents(from rawInput: String) -> (json: String?, remainder: String) {
    let input = rawInput.trimmingLeadingCharacters(in: .whitespacesAndNewlines)
    guard !input.isEmpty else {
        return (nil, "")
    }

    // Handle raw JSON without SSE format (no data: prefix)
    if input.first == "{" || input.first == "[" {
        // Try to find the matching closing brace/bracket to extract a complete JSON object
        if let json = extractRawJSON(from: String(input)) {
            return (json, "")
        }
    }

    guard let newlineRange = input.range(of: "\r\n") ?? input.range(of: "\n") else {
        return (nil, String(input))
    }

    // Extract the first line (up to, but not including, the newline)
    let firstLine = input[..<newlineRange.lowerBound]
    // Everything after the newline is the remainder.
    let remainder = input[newlineRange.upperBound...]

    // Skip all SSE control lines that aren't data
    if firstLine.hasPrefix("event:") ||
       firstLine.hasPrefix("id:") ||
       firstLine.hasPrefix("retry:") ||
       firstLine.hasPrefix(":") ||  // Comments
       firstLine.trimmingCharacters(in: .whitespaces).isEmpty {
        return SplitServerSentEvents(from: String(remainder))
    }
    // Ensure the line starts with "data:".
    let prefix = "data:"
    guard firstLine.hasPrefix(prefix) else {
        // If not, we can't extract a valid JSON object.
        return (nil, String(input))
    }

    // Remove the prefix and trim whitespace to get the JSON object.
    let jsonPart = firstLine.dropFirst(prefix.count).trimmingCharacters(in: .whitespaces)

    return (String(jsonPart), String(remainder))
}

private func extractRawJSON(from input: String) -> String? {
    var depth = 0
    var inString = false
    var escaped = false
    let startChar = input.first!
    let endChar: Character = startChar == "{" ? "}" : "]"

    var position = input.startIndex
    for char in input {
        if escaped {
            escaped = false
            position = input.index(after: position)
            continue
        }
        if char == "\\" && inString {
            escaped = true
            position = input.index(after: position)
            continue
        }
        if char == "\"" {
            inString.toggle()
            position = input.index(after: position)
            continue
        }
        if !inString {
            if char == startChar {
                depth += 1
            } else if char == endChar {
                depth -= 1
                if depth == 0 {
                    let json = String(input.prefix(through: position))
                    // Validate it's actual JSON
                    if let data = json.data(using: String.Encoding.utf8),
                       (try? JSONSerialization.jsonObject(with: data)) != nil {
                        return json
                    }
                    return nil
                }
            }
        }
        position = input.index(after: position)
    }
    return nil
}

