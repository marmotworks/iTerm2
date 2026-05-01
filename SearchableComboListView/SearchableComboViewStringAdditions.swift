//
//  SearchableComboViewStringAdditions.swift
//  SearchableComboListView
//
//  Created by George Nachman on 1/24/20.
//

import Foundation

extension String {
    var tokens: [String] {
        var words: [String] = []
        enumerateSubstrings(
            in: startIndex..<endIndex,
            options: .byWords) { substring, _, _, _ in
                if let substring = substring {
                    words.append(substring.localizedLowercase)
                }
        }
        return words
    }
}
