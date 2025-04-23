#pragma once

#include "AnimSourceData.h"
#include "Charset.h"
#include "PetsciiReader.h"

namespace AnimToolTest {
    struct ChannelCharacterRamTest;
}

namespace AnimTool {

    class ChannelCharacterRam : public SourceChannel {
       public:
        struct Frame {
            uint8_t m_characterRam[1000]{};
            uint8_t m_charsetIndex{};
            uint16_t m_delayMs{};
        };

        void addFramesFromPetscii(const PetsciiAnim& anim, std::optional<Charset> charset);

        void reduceCharsets(int targetCharsetCount, int characterSimilarityThresholdPercentage = 80);

        [[nodiscard]] Type getType() const override { return Type::CHARACTER_RAM; }

        friend struct AnimToolTest::ChannelCharacterRamTest;

       private:
        std::vector<Frame> m_frames;
        std::vector<Charset> m_charsets;
    };
}  // namespace AnimTool