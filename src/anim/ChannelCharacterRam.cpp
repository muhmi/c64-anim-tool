#include "ChannelCharacterRam.h"

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

void ChannelCharacterRam::reduceCharsets(int targetCharsetCount) {

}
