#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "anim/Charset.h"

using namespace AnimTool;

TEST_CASE("Char construction and basic operations", "[char]") {
    // Create test bitmap patterns
    uint8_t pattern0[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};  // All zeros
    uint8_t pattern1[8] = {0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};  // One bit set
    uint8_t pattern2[8] = {0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA};  // All 10101010

    SECTION("Constructor correctly initializes bitmap") {
        Char c(pattern2);
        REQUIRE(std::memcmp(c.data(), pattern2, 8) == 0);
    }

    SECTION("clear() zeroes out the bitmap") {
        Char c(pattern2);
        c.clear();
        REQUIRE(std::memcmp(c.data(), pattern0, 8) == 0);
    }

    SECTION("invert() correctly inverts all bits") {
        Char c(pattern2);  // 0xAA = 10101010
        c.invert();
        // After inversion, should be 01010101 = 0x55
        uint8_t expected[8] = {0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55};
        REQUIRE(std::memcmp(c.data(), expected, 8) == 0);
    }

    SECTION("hash() returns consistent values") {
        Char c1(pattern1);
        Char c2(pattern1);
        Char c3(pattern2);

        REQUIRE(c1.hash() == c2.hash());
        REQUIRE(c1.hash() != c3.hash());
    }
}

TEST_CASE("Char distance calculation", "[char][distance]") {
    // Create test bitmap patterns
    uint8_t pattern0[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};  // All zeros
    uint8_t pattern1[8] = {0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};  // One bit set
    uint8_t pattern2[8] = {0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA};  // All 10101010
    uint8_t pattern3[8] = {0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55};  // All 01010101
    uint8_t pattern4[8] = {0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0};  // Specific pattern
    uint8_t pattern5[8] = {0x21, 0x43, 0x65, 0x87, 0xA9, 0xCB, 0xED, 0x0F};  // Different pattern

    SECTION("Distance between identical characters is zero") {
        Char c1(pattern0);
        Char c2(pattern0);
        REQUIRE(c1.distance(c2) == 0);
        REQUIRE(c2.distance(c1) == 0);
    }

    SECTION("Distance calculation is correct for one bit difference") {
        Char c1(pattern0);  // All zeros
        Char c2(pattern1);  // One bit set
        REQUIRE(c1.distance(c2) == 1);
        REQUIRE(c2.distance(c1) == 1);
    }

    SECTION("Distance calculation is correct for alternating patterns") {
        Char c1(pattern2);  // All 0xAA (10101010...)
        Char c2(pattern3);  // All 0x55 (01010101...)
        // All bits are different, so 8 bytes * 8 bits = 64 differences
        REQUIRE(c1.distance(c2) == 64);
        REQUIRE(c2.distance(c1) == 64);
    }

    SECTION("Distance calculation is correct for specific patterns") {
        Char c1(pattern4);  // Pattern from pattern4
        Char c2(pattern5);  // Pattern from pattern5

        // Calculate expected Hamming distance for the test patterns
        uint16_t expectedDistance = 0;
        for (int i = 0; i < 8; i++) {
            uint8_t xor_result = pattern4[i] ^ pattern5[i];
            while (xor_result) {
                expectedDistance += xor_result & 1;
                xor_result >>= 1;
            }
        }

        REQUIRE(c1.distance(c2) == expectedDistance);
        REQUIRE(c2.distance(c1) == expectedDistance);
    }

    SECTION("Equality operator uses distance") {
        Char c1(pattern0);  // All zeros
        Char c2(pattern0);  // All zeros (same)
        Char c3(pattern1);  // One bit different

        REQUIRE(c1 == c2);        // Should be true (identical)
        REQUIRE_FALSE(c1 == c3);  // Should be false (one bit different)
        REQUIRE_FALSE(c1 != c2);  // Should be false (identical)
        REQUIRE(c1 != c3);        // Should be true (one bit different)
    }

    SECTION("Distance function matches direct hamming_distance_8bytes call") {
        Char c1(pattern4);  // Pattern from pattern4
        Char c2(pattern5);  // Pattern from pattern5

        // Direct call to the hamming distance function
        uint16_t direct_distance =
            hamming_distance_8bytes(c1.data(),  // Direct access to bitmap data
                                    c2.data()   // Direct access to bitmap data
            );

        // Should match the value from the Char class method
        REQUIRE(c1.distance(c2) == direct_distance);
    }
}

TEST_CASE("Charset operations", "[charset]") {
    // Create test characters with different patterns
    uint8_t pattern0[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};  // All zeros
    uint8_t pattern1[8] = {0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};  // One bit set
    uint8_t pattern2[8] = {0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xAA};  // All 10101010

    Char c0(pattern0);
    Char c1(pattern1);
    Char c2(pattern2);

    SECTION("Characters can be inserted and retrieved") {
        Charset charset("test.charset");
        uint8_t idx0 = charset.insert(c0);
        uint8_t idx1 = charset.insert(c1);
        uint8_t idx2 = charset.insert(c2);

        REQUIRE(idx0 == 0);
        REQUIRE(idx1 == 1);
        REQUIRE(idx2 == 2);

        Char retrieved0 = charset[0];
        Char retrieved1 = charset[1];
        Char retrieved2 = charset[2];

        REQUIRE(retrieved0 == c0);
        REQUIRE(retrieved1 == c1);
        REQUIRE(retrieved2 == c2);
    }

    SECTION("Duplicate characters are not inserted multiple times") {
        Charset charset("test.charset");
        uint8_t idx0 = charset.insert(c0);
        uint8_t idx1 = charset.insert(c1);

        // Try to insert the same character again
        uint8_t idx0_again = charset.insert(c0);

        REQUIRE(idx0 == 0);
        REQUIRE(idx1 == 1);
        REQUIRE(idx0_again == idx0);  // Should return the same index

        // Verify size is still 2
        REQUIRE(charset.insert(c2) == 2);  // This would be index 2 (third character)
    }

    SECTION("Charset equality considers both characters and filename") {
        // Create identical charsets with same filename
        Charset charset1("same.charset");
        Charset charset2("same.charset");

        charset1.insert(c0);
        charset1.insert(c1);

        charset2.insert(c0);
        charset2.insert(c1);

        // Should be equal when characters and filenames match
        REQUIRE(charset1 == charset2);

        // Create charsets with different filenames but same characters
        Charset charset3("different1.charset");
        Charset charset4("different2.charset");

        charset3.insert(c0);
        charset3.insert(c1);

        charset4.insert(c0);
        charset4.insert(c1);

        // Should not be equal due to different filenames
        REQUIRE(charset3 != charset4);

        // Create charsets with same filename but different characters
        Charset charset5("same.charset");
        Charset charset6("same.charset");

        charset5.insert(c0);
        charset5.insert(c1);

        charset6.insert(c0);
        charset6.insert(c2);  // Different character

        // Should not be equal due to different characters
        REQUIRE(charset5 != charset6);
    }

    SECTION("Charset equality handles different character counts") {
        Charset charset1("same.charset");
        Charset charset2("same.charset");

        charset1.insert(c0);
        charset1.insert(c1);

        charset2.insert(c0);
        charset2.insert(c1);
        charset2.insert(c2);  // Extra character

        // Should not be equal due to different character counts
        REQUIRE(charset1 != charset2);
    }

    SECTION("Charset hash function includes both characters and filename") {
        // Charsets with same filename and characters should have same hash
        Charset charset1("same.charset");
        Charset charset2("same.charset");

        charset1.insert(c0);
        charset1.insert(c1);

        charset2.insert(c0);
        charset2.insert(c1);

        REQUIRE(charset1.hash() == charset2.hash());

        // Charsets with different filenames should have different hashes
        Charset charset3("different1.charset");
        charset3.insert(c0);
        charset3.insert(c1);

        REQUIRE(charset1.hash() != charset3.hash());

        // Charsets with different characters should have different hashes
        Charset charset4("same.charset");
        charset4.insert(c0);
        charset4.insert(c2);  // Different character

        REQUIRE(charset1.hash() != charset4.hash());
    }
}