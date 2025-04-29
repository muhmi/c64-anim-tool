#include "ChannelCharacterRam.h"

#include <unordered_set>

#include "fmt/format.h"

using namespace AnimTool;

void AnimTool::ChannelCharacterRam::addFramesFromPetscii(const PetsciiAnim &anim, std::optional<Charset> charset) {
    size_t charset_index = 0;
    if (charset) {
        if (auto it = std::find(m_charsets.begin(), m_charsets.end(), *charset); it != m_charsets.end()) {
            charset_index = std::distance(m_charsets.begin(), it);
        } else {
            charset_index = m_charsets.size();
            m_charsets.push_back(*charset);
        }
    }
    for (const auto &petsciiFrame : anim.m_frames) {
        Frame frame;
        frame.m_charsetIndex = static_cast<uint8_t>(charset_index);
        frame.m_delayMs = petsciiFrame.m_delayMs;
        for (size_t idx = 0; idx < 1000; ++idx) {
            frame.m_characterRam[idx] = static_cast<uint8_t>(petsciiFrame.m_characterRam[idx]);
        }
    }
}

void ChannelCharacterRam::reduceCharsets(const int maxCharsetCount) {
    // Step 1: Collect all unique characters used across all frames
    std::unordered_set<Char> all_characters;
    all_characters.insert(Char::BLANK);
    all_characters.insert(Char::FULL);

    for (const auto &frame : m_frames) {
        const auto &charset = m_charsets[frame.m_charsetIndex];
        for (unsigned char idx : frame.m_characterRam) {
            all_characters.insert(charset[idx]);
        }
    }

    const int uniqueCharCount = static_cast<int>(all_characters.size());

    // Check if all characters can fit into a single charset
    if (uniqueCharCount <= 256) {
        // Simple case: All characters fit in one charset
        Charset new_charset("generated_by_reduceCharsets");
        new_charset.insert(Char::BLANK);
        new_charset.insert(Char::FULL);

        for (const auto &chr : all_characters) {
            new_charset.insert(chr);
        }

        // Create new frames with remapped character indices
        std::vector<Frame> new_frames;
        for (const auto &frame : m_frames) {
            const auto &old_charset = m_charsets[frame.m_charsetIndex];
            Frame new_frame;
            new_frame.m_charsetIndex = 0;
            new_frame.m_delayMs = frame.m_delayMs;

            for (int idx = 0; idx < 1000; ++idx) {
                Char old_char = old_charset[frame.m_characterRam[idx]];
                if (auto newIndex = new_charset.indexOf(old_char); newIndex) {
                    new_frame.m_characterRam[idx] = *newIndex;
                } else {
                    // This shouldn't happen as we've added all chars, but just in case
                    new_frame.m_characterRam[idx] = 0;  // Use BLANK as fallback
                }
            }
            new_frames.push_back(new_frame);
        }

        // Replace old charsets and frames
        m_charsets = {new_charset};
        m_frames = std::move(new_frames);
        return;
    }

    // Complex case: Need to distribute characters across multiple charsets

    // Step 2: Count character usage to prioritize common characters
    std::unordered_map<Char, int> use_counts;
    use_counts[Char::BLANK] = 1;
    use_counts[Char::FULL] = 1;

    for (const auto &frame : m_frames) {
        const auto &charset = m_charsets[frame.m_charsetIndex];
        for (unsigned char idx : frame.m_characterRam) {
            auto chr = charset[idx];
            use_counts[chr]++;
        }
    }

    // Sort characters by usage frequency
    std::vector<std::pair<Char, int>> char_counts;
    char_counts.reserve(use_counts.size());
    for (const auto &[chr, count] : use_counts) {
        char_counts.emplace_back(chr, count);
    }

    std::sort(char_counts.begin(), char_counts.end(), [](const auto &a, const auto &b) { return a.second > b.second; });

    // Step 3: Create new charsets with globally most used characters
    std::vector<Charset> new_charsets;
    const int maxCharsPerSet = 256;  // C64 charset size

    // Create target number of charsets with BLANK and FULL
    for (int i = 0; i < maxCharsetCount; i++) {
        Charset new_charset(fmt::format("generated_by_reduceCharsets_{}_{}", maxCharsetCount, i));
        new_charset.insert(Char::BLANK);
        new_charset.insert(Char::FULL);
        new_charsets.push_back(new_charset);
    }

    // Add the most globally used characters to ALL charsets first
    // This ensures common characters are available in every charset
    int globalCharCount = std::min(static_cast<int>(char_counts.size()), 50);
    for (int i = 0; i < globalCharCount && i < static_cast<int>(char_counts.size()); i++) {
        const auto &ch = char_counts[i].first;
        for (auto &charset : new_charsets) {
            if (charset.size() < maxCharsPerSet) {
                charset.insert(ch);
            }
        }
    }

    // Step 4: Group frames into maxCharsetCount groups
    // Ideally, we want to keep frames with similar character usage together
    std::vector<std::vector<int>> frame_groups(maxCharsetCount);

    // Start with first frame in first group
    if (!m_frames.empty()) {
        frame_groups[0].push_back(0);
    }

    // Group remaining frames based on similarity to previous frame or group size
    for (size_t i = 1; i < m_frames.size(); i++) {
        const auto &curr_frame = m_frames[i];
        const auto &prev_frame = m_frames[i - 1];

        // Try to keep sequential frames together if possible
        int prev_group = -1;
        for (int g = 0; g < maxCharsetCount; g++) {
            if (!frame_groups[g].empty() && frame_groups[g].back() == static_cast<int>(i - 1)) {
                prev_group = g;
                break;
            }
        }

        // Find a group with similar character usage
        if (prev_group != -1) {
            int same_chars = 0;
            for (int j = 0; j < 1000; j++) {
                if (curr_frame.m_characterRam[j] == prev_frame.m_characterRam[j]) {
                    same_chars++;
                }
            }

            // If frames share more than 60% of their characters, keep them together
            if (same_chars > 600) {
                frame_groups[prev_group].push_back(static_cast<int>(i));
                continue;
            }
        }

        // Otherwise, add to the smallest group to balance sizes
        int min_group_size = std::numeric_limits<int>::max();
        int min_group_idx = 0;

        for (int g = 0; g < maxCharsetCount; g++) {
            if (static_cast<int>(frame_groups[g].size()) < min_group_size) {
                min_group_size = static_cast<int>(frame_groups[g].size());
                min_group_idx = g;
            }
        }

        frame_groups[min_group_idx].push_back(static_cast<int>(i));
    }

    // Step 5: Fill each charset with characters specific to its frame group
    std::unordered_map<Char, int> added_chars;
    for (const auto &[chr, _] : use_counts) {
        added_chars[chr] = 0;  // Mark all as not added yet
    }

    // Mark globally added characters
    for (int i = 0; i < globalCharCount && i < static_cast<int>(char_counts.size()); i++) {
        added_chars[char_counts[i].first] = maxCharsetCount;  // Added to all charsets
    }

    // For each group, add most frequent characters from its frames
    for (int g = 0; g < maxCharsetCount; g++) {
        auto &charset = new_charsets[g];
        std::unordered_map<Char, int> group_char_counts;

        // Count characters in this group's frames
        for (int frame_idx : frame_groups[g]) {
            const auto &frame = m_frames[frame_idx];
            const auto &old_charset = m_charsets[frame.m_charsetIndex];

            for (unsigned char idx : frame.m_characterRam) {
                auto chr = old_charset[idx];
                group_char_counts[chr]++;
            }
        }

        // Sort characters by frequency in this group
        std::vector<std::pair<Char, int>> group_chars;
        for (const auto &[chr, count] : group_char_counts) {
            if (added_chars[chr] < maxCharsetCount) {  // Skip if already in all charsets
                group_chars.emplace_back(chr, count);
            }
        }

        std::sort(group_chars.begin(), group_chars.end(),
                  [](const auto &a, const auto &b) { return a.second > b.second; });

        // Add characters to this charset until full
        for (const auto &[chr, _] : group_chars) {
            if (charset.size() < maxCharsPerSet) {
                charset.insert(chr);
                added_chars[chr]++;
            } else {
                break;
            }
        }
    }

    // Step 6: Map frames to new charsets
    std::vector<Frame> new_frames;

    // Helper function to find closest character in a charset
    auto findClosestChar = [](const Char &target, const Charset &charset) -> uint8_t {
        uint8_t best_idx = 0;
        uint16_t min_distance = std::numeric_limits<uint16_t>::max();

        for (size_t i = 0; i < charset.size(); i++) {
            uint16_t dist = target.distance(charset[i]);
            if (dist < min_distance) {
                min_distance = dist;
                best_idx = static_cast<uint8_t>(i);
            }
        }

        return best_idx;
    };

    for (size_t i = 0; i < m_frames.size(); i++) {
        const auto &frame = m_frames[i];
        const auto &old_charset = m_charsets[frame.m_charsetIndex];

        // Find which group this frame belongs to
        int group_idx = 0;
        for (int g = 0; g < maxCharsetCount; g++) {
            if (std::find(frame_groups[g].begin(), frame_groups[g].end(), i) != frame_groups[g].end()) {
                group_idx = g;
                break;
            }
        }

        // Create new frame using the group's charset
        Frame new_frame;
        new_frame.m_charsetIndex = group_idx;
        new_frame.m_delayMs = frame.m_delayMs;

        // Map each character to new charset
        for (int j = 0; j < 1000; j++) {
            Char old_char = old_charset[frame.m_characterRam[j]];
            if (auto new_idx = new_charsets[group_idx].indexOf(old_char); new_idx) {
                new_frame.m_characterRam[j] = *new_idx;
            } else {
                // If character not found in new charset, find closest match
                new_frame.m_characterRam[j] = findClosestChar(old_char, new_charsets[group_idx]);
            }
        }

        new_frames.push_back(new_frame);
    }

    // Replace old charsets and frames with new ones
    m_charsets = std::move(new_charsets);
    m_frames = std::move(new_frames);
}