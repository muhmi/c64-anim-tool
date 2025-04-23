#include "ChannelCharacterRam.h"

#include <unordered_set>

#include "fmt/format.h"

using namespace AnimTool;

void AnimTool::ChannelCharacterRam::addFramesFromPetscii(const PetsciiAnim &anim,
                                                         std::optional<Charset> charset) {
    size_t charset_index = 0;
    if (charset) {
        if (auto it = std::find(m_charsets.begin(), m_charsets.end(), *charset);
            it != m_charsets.end()) {
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

void ChannelCharacterRam::reduceCharsets(const int targetCharsetCount,
                                         const int characterSimilarityThresholdPercentage) {
    if (static_cast<int>(m_charsets.size()) <= targetCharsetCount) return;

    // Count character usage across all frames
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

    std::sort(char_counts.begin(), char_counts.end(),
              [](const auto &a, const auto &b) { return a.second > b.second; });

    // Phase 1: Create new charsets with globally most used characters
    std::vector<Charset> new_charsets;
    int maxCharsPerSet = 256;  // C64 charset size

    // Create target number of charsets with BLANK and FULL
    for (int i = 0; i < targetCharsetCount; i++) {
        Charset new_charset(
            fmt::format("generated_by_reduceCharsets_{}_{}", targetCharsetCount, i));
        new_charset.insert(Char::BLANK);
        new_charset.insert(Char::FULL);
        new_charsets.push_back(new_charset);
    }

    // Add the most globally used characters to ALL charsets first
    int globalCharCount = std::min(static_cast<int>(char_counts.size()), 50);
    for (int i = 0; i < globalCharCount; i++) {
        const auto &ch = char_counts[i].first;
        for (auto &charset : new_charsets) {
            if (static_cast<int>(charset.size()) < maxCharsPerSet) {
                charset.insert(ch);
            }
        }
    }

    // Phase 2: Group frames into targetCharsetCount groups based on similarity
    //
    // Idea is to try to keep frames with similar chars using same charsets
    //
    // How similar the frames need to be, is controlled by giving a percentage as arg
    // `characterSimilarityThresholdPercentage`

    std::vector<std::vector<int>> frame_groups(targetCharsetCount);
    frame_groups[0].push_back(0);

    const int threshold = std::clamp(characterSimilarityThresholdPercentage * 10, 0, 1000);

    for (size_t i = 1; i < m_frames.size(); i++) {
        const auto &curr_frame = m_frames[i];
        const auto &prev_frame = m_frames[i - 1];

        // Try to keep sequential frames together
        int prev_group = -1;
        for (int g = 0; g < targetCharsetCount; g++) {
            if (!frame_groups[g].empty() && frame_groups[g].back() == static_cast<int>(i - 1)) {
                prev_group = g;
                break;
            }
        }

        // Find a group with enough similar characters
        if (prev_group != -1) {
            int same_chars = 0;
            for (int j = 0; j < 1000; j++) {
                if (curr_frame.m_characterRam[j] == prev_frame.m_characterRam[j]) {
                    same_chars++;
                }
            }

            if (same_chars > threshold) {
                frame_groups[prev_group].push_back(static_cast<int>(i));
                continue;
            }
        }

        // Ok, just use the smallest group instead
        int min_group_size = std::numeric_limits<int>::max();
        int min_group_idx = 0;

        for (int g = 0; g < targetCharsetCount; g++) {
            if (static_cast<int>(frame_groups[g].size()) < min_group_size) {
                min_group_size = static_cast<int>(frame_groups[g].size());
                min_group_idx = g;
            }
        }

        frame_groups[min_group_idx].push_back(static_cast<int>(i));
    }

    // Phase 3: Populate each charset with characters specific to its frame group
    std::unordered_map<Char, int> added_chars;
    for (const auto &ch : char_counts) {
        added_chars[ch.first] = 0;  // Mark all as not added yet
    }

    // Mark globally added characters
    for (int i = 0; i < globalCharCount; i++) {
        added_chars[char_counts[i].first] = targetCharsetCount;  // Added to all charsets
    }

    // For each group, add most frequent characters from its frames
    for (int g = 0; g < targetCharsetCount; g++) {
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
            if (added_chars[chr] < targetCharsetCount) {  // Skip if already in all charsets
                group_chars.emplace_back(chr, count);
            }
        }

        std::sort(group_chars.begin(), group_chars.end(),
                  [](const auto &a, const auto &b) { return a.second > b.second; });

        // Add characters to this charset
        for (const auto &[chr, count] : group_chars) {
            if (static_cast<int>(charset.size()) < maxCharsPerSet) {
                charset.insert(chr);
                added_chars[chr]++;
            } else {
                break;
            }
        }
    }

    // Phase 4: Create lookup tables for each original charset to find the closest matches in new
    // charsets
    std::vector<std::vector<std::vector<uint8_t>>> charset_mappings(
        m_charsets.size(),
        std::vector<std::vector<uint8_t>>(256, std::vector<uint8_t>(targetCharsetCount)));

    for (size_t old_charset_idx = 0; old_charset_idx < m_charsets.size(); old_charset_idx++) {
        const auto &old_charset = m_charsets[old_charset_idx];

        for (int old_char_idx = 0; old_char_idx < 256; old_char_idx++) {
            if (old_char_idx >= static_cast<int>(old_charset.size())) break;

            auto old_char = old_charset[old_char_idx];

            // Find the closest match in each new charset
            for (int new_charset_idx = 0; new_charset_idx < targetCharsetCount; new_charset_idx++) {
                const auto &new_charset = new_charsets[new_charset_idx];

                uint8_t best_idx = 0;
                uint16_t min_distance = std::numeric_limits<uint16_t>::max();

                for (size_t j = 0; j < new_charset.size(); j++) {
                    uint16_t dist = old_char.distance(new_charset[j]);
                    if (dist < min_distance) {
                        min_distance = dist;
                        best_idx = j;
                    }
                }

                charset_mappings[old_charset_idx][old_char_idx][new_charset_idx] = best_idx;
            }
        }
    }

    // Phase 5: Assign charsets to frames based on frame groups
    std::vector<Frame> new_frames;

    for (size_t i = 0; i < m_frames.size(); i++) {
        const auto &frame = m_frames[i];
        int old_charset_idx = frame.m_charsetIndex;

        // Find which group this frame belongs to
        int group_idx = 0;
        for (int g = 0; g < targetCharsetCount; g++) {
            if (std::find(frame_groups[g].begin(), frame_groups[g].end(), i) !=
                frame_groups[g].end()) {
                group_idx = g;
                break;
            }
        }

        // Create new frame using the group's charset
        Frame new_frame;
        new_frame.m_charsetIndex = group_idx;
        new_frame.m_delayMs = frame.m_delayMs;

        // Map each character to the closest match in new charset
        for (int j = 0; j < 1000; j++) {
            uint8_t old_char_idx = frame.m_characterRam[j];
            new_frame.m_characterRam[j] =
                charset_mappings[old_charset_idx][old_char_idx][group_idx];
        }

        new_frames.push_back(new_frame);
    }

    // Phase 6: Replace old charsets and frames with new ones
    m_charsets = std::move(new_charsets);
    m_frames = std::move(new_frames);
}
