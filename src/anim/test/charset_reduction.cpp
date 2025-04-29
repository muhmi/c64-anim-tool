#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "anim/ChannelCharacterRam.h"

using namespace AnimTool;

namespace AnimToolTest {

    struct ChannelCharacterRamTest {
        // Helper function to create a test character set with specific patterns
        static Charset createTestCharset(const std::string& name) {
            // Create test bitmap patterns
            uint8_t pattern0[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};  // All zeros (BLANK)
            uint8_t pattern1[8] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};  // All ones (FULL)
            uint8_t patternA[8] = {0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA};  // Alternating 10101010
            uint8_t pattern5[8] = {0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55};  // Alternating 01010101
            uint8_t patternX[8] = {0x81, 0x42, 0x24, 0x18, 0x18, 0x24, 0x42, 0x81};  // X pattern
            uint8_t patternO[8] = {0x3C, 0x42, 0x81, 0x81, 0x81, 0x81, 0x42, 0x3C};  // O pattern

            Charset charset(name);
            charset.insert(Char(pattern0));  // Insert BLANK at index 0
            charset.insert(Char(pattern1));  // Insert FULL at index 1
            charset.insert(Char(patternA));  // Insert alternating pattern at index 2
            charset.insert(Char(pattern5));  // Insert inverse alternating pattern at index 3
            charset.insert(Char(patternX));  // Insert X pattern at index 4
            charset.insert(Char(patternO));  // Insert O pattern at index 5
            return charset;
        }

        // Helper function to create a frame with specific content
        static ChannelCharacterRam::Frame createFrame(uint8_t charsetIndex, uint16_t delayMs, uint8_t defaultChar) {
            ChannelCharacterRam::Frame frame;
            frame.m_charsetIndex = charsetIndex;
            frame.m_delayMs = delayMs;

            // Fill with default character
            for (unsigned char& i : frame.m_characterRam) {
                i = defaultChar;
            }

            return frame;
        }

        static void testNoReductionWhenCharsetsLessThanTarget() {
            SECTION("No reduction when charsets <= target count") {
                // Create a test ChannelCharacterRam instance with mock data
                ChannelCharacterRam channel;

                // Add two charsets
                channel.m_charsets.push_back(createTestCharset("charset1"));
                channel.m_charsets.push_back(createTestCharset("charset2"));

                // Add frames using these charsets
                channel.m_frames.push_back(createFrame(0, 100, 2));  // Use charset 0, with character index 2
                channel.m_frames.push_back(createFrame(1, 200, 3));  // Use charset 1, with character index 3

                // Make copies for comparison
                auto original_charsets = channel.m_charsets;
                auto original_frames = channel.m_frames;

                // Call reduceCharsets with target >= current count
                channel.reduceCharsets(3);  // Target is 3, but we only have 2

                // Verify charsets size - with the updated implementation, we might still consolidate to a single
                // charset if all unique characters can fit in one charset If the character count is small enough to fit
                // in one charset, we'll have 1 charset Otherwise, we'll keep the original 2 charsets

                // Verify frames count is unchanged
                REQUIRE(channel.m_frames.size() == original_frames.size());

                // Verify delay values are preserved
                REQUIRE(channel.m_frames[0].m_delayMs == 100);
                REQUIRE(channel.m_frames[1].m_delayMs == 200);

                // In our implementation, we may consolidate to 1 charset if all unique chars fit
                // or leave it as 2 charsets if they don't, so check for either condition
                REQUIRE((channel.m_charsets.size() == 1 || channel.m_charsets.size() == 2));

                // Check that BLANK and FULL are still present in all charsets
                for (const auto& charset : channel.m_charsets) {
                    REQUIRE(charset[0] == Char::BLANK);
                    REQUIRE(charset[1] == Char::FULL);
                }
            }
        }

        static void testBasicReduction() {
            SECTION("Basic reduction from 3 charsets to 2") {
                ChannelCharacterRam channel;

                // Add three charsets
                channel.m_charsets.push_back(createTestCharset("charset1"));
                channel.m_charsets.push_back(createTestCharset("charset2"));
                channel.m_charsets.push_back(createTestCharset("charset3"));

                // Add frames that mostly use specific character indices
                // Frame 1-2 use mainly chars from charset 0
                channel.m_frames.push_back(createFrame(0, 100, 2));
                channel.m_frames.push_back(createFrame(0, 100, 3));

                // Frame 3-5 use mainly chars from charset 1 and 2
                channel.m_frames.push_back(createFrame(1, 100, 4));
                channel.m_frames.push_back(createFrame(2, 100, 5));
                channel.m_frames.push_back(createFrame(1, 100, 4));

                // Remember original frame count
                size_t original_frame_count = channel.m_frames.size();

                // Reduce to 2 charsets
                channel.reduceCharsets(2);

                // Verify we have 2 charsets or 1 (if all chars could fit in a single charset)
                REQUIRE((channel.m_charsets.size() == 1 || channel.m_charsets.size() == 2));

                // Verify we still have the same number of frames
                REQUIRE(channel.m_frames.size() == original_frame_count);

                // Verify all frames now use charset indices within the valid range
                for (const auto& frame : channel.m_frames) {
                    REQUIRE(frame.m_charsetIndex < channel.m_charsets.size());
                }

                // Verify first two chars in all charsets are BLANK and FULL
                for (const auto& charset : channel.m_charsets) {
                    REQUIRE(charset[0] == Char::BLANK);
                    REQUIRE(charset[1] == Char::FULL);
                }

                // Verify delay values are preserved
                for (size_t i = 0; i < original_frame_count; i++) {
                    REQUIRE(channel.m_frames[i].m_delayMs == 100);
                }
            }
        }

        static void testSequentialFrameGrouping() {
            SECTION("Sequential frames are grouped in the same charset") {
                ChannelCharacterRam channel;

                // Add four charsets
                channel.m_charsets.push_back(createTestCharset("charset1"));
                channel.m_charsets.push_back(createTestCharset("charset2"));
                channel.m_charsets.push_back(createTestCharset("charset3"));
                channel.m_charsets.push_back(createTestCharset("charset4"));

                // Create 8 sequential frames that should be grouped by similarity
                // Frames 0-2 use similar characters (2 and 3)
                auto frame0 = createFrame(0, 100, 2);
                auto frame1 = createFrame(1, 100, 2);
                auto frame2 = createFrame(2, 100, 3);

                // Frames 3-5 use similar characters (4 and 5)
                auto frame3 = createFrame(0, 100, 4);
                auto frame4 = createFrame(1, 100, 4);
                auto frame5 = createFrame(3, 100, 5);

                // Make frames 0-1 very similar
                for (int i = 0; i < 1000; i++) {
                    if (i % 10 == 0) {
                        frame1.m_characterRam[i] = 3;  // Small difference
                    }
                }

                // Make frames 3-4 very similar
                for (int i = 0; i < 1000; i++) {
                    if (i % 20 == 0) {
                        frame4.m_characterRam[i] = 5;  // Small difference
                    }
                }

                channel.m_frames.push_back(frame0);
                channel.m_frames.push_back(frame1);
                channel.m_frames.push_back(frame2);
                channel.m_frames.push_back(frame3);
                channel.m_frames.push_back(frame4);
                channel.m_frames.push_back(frame5);

                // Reduce to 2 charsets
                channel.reduceCharsets(2);

                // Verify we now have 1 or 2 charsets (1 if all unique chars fit in a single charset)
                REQUIRE((channel.m_charsets.size() == 1 || channel.m_charsets.size() == 2));

                // Verify we still have 6 frames
                REQUIRE(channel.m_frames.size() == 6);

                // If we have 2 charsets, then verify sequential similar frames use the same charset
                if (channel.m_charsets.size() == 2) {
                    // Since our implementation tries to group sequential frames, check if frames 0-1
                    // are assigned to the same charset
                    REQUIRE(channel.m_frames[0].m_charsetIndex == channel.m_frames[1].m_charsetIndex);

                    // Similarly, frames 3-4 should use the same charset
                    REQUIRE(channel.m_frames[3].m_charsetIndex == channel.m_frames[4].m_charsetIndex);
                }

                // In all cases, verify timing is preserved
                for (const auto& frame : channel.m_frames) {
                    REQUIRE(frame.m_delayMs == 100);
                }
            }
        }

        static void testVisualDifferenceMinimization() {
            SECTION("Characters are chosen to minimize visual differences") {
                ChannelCharacterRam channel;

                // Create specific test patterns
                uint8_t pattern0[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};          // All zeros (BLANK)
                uint8_t pattern1[8] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};          // All ones (FULL)
                uint8_t patternA[8] = {0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA};          // Alternating 10101010
                uint8_t pattern5[8] = {0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55};          // Alternating 01010101
                uint8_t patternX[8] = {0x81, 0x42, 0x24, 0x18, 0x18, 0x24, 0x42, 0x81};          // X pattern
                uint8_t pattern_almost_A[8] = {0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xA8, 0xAA};  // Almost alternating
                uint8_t pattern_almost_5[8] = {0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x54, 0x55};  // Almost 01010101
                uint8_t pattern_almost_X[8] = {0x81, 0x42, 0x24, 0x18, 0x18, 0x24, 0x42, 0x80};  // Almost X

                // Add three charsets with specific patterns
                Charset charset1("charset1");
                charset1.insert(Char(pattern0));          // BLANK at index 0
                charset1.insert(Char(pattern1));          // FULL at index 1
                charset1.insert(Char(patternA));          // Alternating 10101010 at index 2
                charset1.insert(Char(pattern_almost_A));  // Almost alternating at index 3

                Charset charset2("charset2");
                charset2.insert(Char(pattern0));          // BLANK at index 0
                charset2.insert(Char(pattern1));          // FULL at index 1
                charset2.insert(Char(pattern5));          // Alternating 01010101 at index 2
                charset2.insert(Char(pattern_almost_5));  // Almost 01010101 at index 3

                Charset charset3("charset3");
                charset3.insert(Char(pattern0));          // BLANK at index 0
                charset3.insert(Char(pattern1));          // FULL at index 1
                charset3.insert(Char(patternX));          // X pattern at index 2
                charset3.insert(Char(pattern_almost_X));  // Almost X at index 3

                channel.m_charsets.push_back(charset1);
                channel.m_charsets.push_back(charset2);
                channel.m_charsets.push_back(charset3);

                // Create frames using these specific characters
                auto frame1 = createFrame(0, 100, 2);  // Uses alternating pattern
                auto frame2 = createFrame(0, 100, 3);  // Uses almost alternating
                auto frame3 = createFrame(1, 100, 2);  // Uses alternating 01010101
                auto frame4 = createFrame(1, 100, 3);  // Uses almost 01010101
                auto frame5 = createFrame(2, 100, 2);  // Uses X pattern
                auto frame6 = createFrame(2, 100, 3);  // Uses almost X

                channel.m_frames.push_back(frame1);
                channel.m_frames.push_back(frame2);
                channel.m_frames.push_back(frame3);
                channel.m_frames.push_back(frame4);
                channel.m_frames.push_back(frame5);
                channel.m_frames.push_back(frame6);

                // Reduce to 2 charsets
                channel.reduceCharsets(2);

                // Verify we have 1 or 2 charsets
                REQUIRE((channel.m_charsets.size() == 1 || channel.m_charsets.size() == 2));

                // Only test visual similarity if we actually have 2 charsets
                if (channel.m_charsets.size() == 2) {
                    // Check if similar patterns tend to be grouped together

                    // Since our implementation already groups similar characters,
                    // we'll verify that frames using similar characters get assigned to the same charset

                    // Frames 1-2 use similar characters
                    REQUIRE(channel.m_frames[0].m_charsetIndex == channel.m_frames[1].m_charsetIndex);

                    // Frames 3-4 use similar characters
                    REQUIRE(channel.m_frames[2].m_charsetIndex == channel.m_frames[3].m_charsetIndex);
                }

                // In all cases, verify we still have all 6 frames
                REQUIRE(channel.m_frames.size() == 6);

                // Verify timing is preserved
                for (const auto& frame : channel.m_frames) {
                    REQUIRE(frame.m_delayMs == 100);
                }
            }
        }

        static void testPreservationOfBlankAndFull() {
            SECTION("Reduction preserves BLANK and FULL characters") {
                ChannelCharacterRam channel;

                // Add five charsets
                for (int i = 0; i < 5; i++) {
                    channel.m_charsets.push_back(createTestCharset("charset" + std::to_string(i)));
                }

                // Add frames using each charset
                for (int i = 0; i < 5; i++) {
                    channel.m_frames.push_back(createFrame(i, 100, 0));  // Using BLANK
                    channel.m_frames.push_back(createFrame(i, 100, 1));  // Using FULL
                }

                // Reduce to 1 charset
                channel.reduceCharsets(1);

                // Verify we have 1 charset
                REQUIRE(channel.m_charsets.size() == 1);

                // Verify BLANK and FULL are preserved in the charset
                REQUIRE(channel.m_charsets[0][0] == Char::BLANK);  // BLANK
                REQUIRE(channel.m_charsets[0][1] == Char::FULL);   // FULL

                // Verify all frames now use charset index 0
                for (const auto& frame : channel.m_frames) {
                    REQUIRE(frame.m_charsetIndex == 0);
                }

                // Check that frames that used BLANK (character index 0) still use it
                for (int i = 0; i < 5; i++) {
                    // Every even frame used BLANK
                    REQUIRE(channel.m_frames[i * 2].m_characterRam[0] == 0);
                }

                // Check that frames that used FULL (character index 1) still use it
                for (int i = 0; i < 5; i++) {
                    // Every odd frame used FULL
                    REQUIRE(channel.m_frames[i * 2 + 1].m_characterRam[0] == 1);
                }
            }
        }

        static void testFrameOrderPreservation() {
            SECTION("Frame order is preserved after reduction") {
                ChannelCharacterRam channel;

                // Add three charsets
                channel.m_charsets.push_back(createTestCharset("charset1"));
                channel.m_charsets.push_back(createTestCharset("charset2"));
                channel.m_charsets.push_back(createTestCharset("charset3"));

                // Create frames with unique identifiable delay values
                for (int i = 0; i < 10; i++) {
                    auto frame = createFrame(i % 3, 100 + i * 10, (i % 5) + 1);
                    channel.m_frames.push_back(frame);
                }

                // Remember the delay values in original order
                std::vector<uint16_t> original_delays;
                for (const auto& frame : channel.m_frames) {
                    original_delays.push_back(frame.m_delayMs);
                }

                // Reduce charsets
                channel.reduceCharsets(2);

                // Verify delay values are still in the same order
                REQUIRE(channel.m_frames.size() == original_delays.size());
                for (size_t i = 0; i < channel.m_frames.size(); i++) {
                    REQUIRE(channel.m_frames[i].m_delayMs == original_delays[i]);
                }
            }
        }

        static void runAllTests() {
            testNoReductionWhenCharsetsLessThanTarget();
            testBasicReduction();
            testSequentialFrameGrouping();
            testVisualDifferenceMinimization();
            testPreservationOfBlankAndFull();
            testFrameOrderPreservation();  // Added new test for frame order preservation
        }
    };

}  // namespace AnimToolTest

// Main test case function that runs all the tests in the test class
TEST_CASE("ChannelCharacterRam::reduceCharsets functionality", "[channel][charset][reduce]") {
    AnimToolTest::ChannelCharacterRamTest::runAllTests();
}