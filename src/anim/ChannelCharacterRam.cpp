#include "ChannelCharacterRam.h"

using namespace AnimTool;

void AnimTool::ChannelCharacterRam::addFramesFromPetscii(const PetsciiAnim &anim, std::optional<Charset> charset) {
    size_t charset_index = 0;
    if (charset) {
        charset_index = m_charsets.size();
        m_charsets.push_back(*charset);
    }
    for (size_t idx = 0; idx < anim.m_frames.size(); ++idx) {
        Frame frame;
        frame.m_charsetIndex = static_cast<uint8_t>(charset_index);
        frame.m_delayMs = anim.m_frames[idx].m_delayMs;
    }

}

void ChannelCharacterRam::reduceCharsets(int targetCharsetCount) {

}
