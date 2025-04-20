#include "ChannelCharacterRam.h"

#include <unordered_set>

using namespace AnimTool;

void AnimTool::ChannelCharacterRam::addFramesFromPetscii(const PetsciiAnim &anim, std::optional<Charset> charset) {
    size_t charset_index = 0;
    if (charset) {
        if (auto it = std::find(m_charsets.begin(), m_charsets.end(), *charset); it != m_charsets.end())
        {
            charset_index = std::distance(m_charsets.begin(), it);
        }
        else {
            charset_index = m_charsets.size();
            m_charsets.push_back(*charset);
        }
    }
    for (const auto & petsciiFrame : anim.m_frames) {
        Frame frame;
        frame.m_charsetIndex = static_cast<uint8_t>(charset_index);
        frame.m_delayMs = petsciiFrame.m_delayMs;
        for (size_t idx = 0; idx < 1000; ++idx) {
            frame.m_characterRam[idx] = static_cast<uint8_t>(petsciiFrame.m_characterRam[idx]);
        }
    }
}

void ChannelCharacterRam::reduceCharsets_PreferFullCharsets(int targetCharsetCount) {
    std::unordered_set<Char> all_chars;
    for (auto& charset : m_charsets) {
        for(uint8_t idx = 0; idx < 0xff; ++idx) {
            all_chars.insert(charset[idx]);
        }
    }
    int requiredCharsets = static_cast<int>(all_chars.size() / 0xff);
    if (requiredCharsets <= targetCharsetCount) {
        
    }
}
