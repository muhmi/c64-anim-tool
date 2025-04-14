#include <catch2/catch_test_macros.hpp>
#include <catch2/catch_approx.hpp>
#include "anim/AnimSourceData.h"

using namespace AnimTool;

TEST_CASE("Char distance calculation", "[char][distance]") {
    // Create a test charset with known data patterns
    Charset charset;
    charset.m_sourceFilename = "test.charset";

    // Setup: We need to prepare the bitmap in the charset
    // Assuming each Char is 8 bytes and is stored in the bitmap at index * 8

    // Set up pattern for char at index 0 (all zeros)
    for (int i = 0; i < 8; i++) {
        charset.m_bitmap[i] = 0x00;
    }

    // Set up pattern for char at index 1 (one bit set)
    for (int i = 0; i < 8; i++) {
        charset.m_bitmap[8 + i] = 0x00;
    }
    charset.m_bitmap[8] = 0x01; // First byte has one bit set

    // Set up pattern for char at index 2 (all 0xAA)
    for (int i = 0; i < 8; i++) {
        charset.m_bitmap[16 + i] = 0xAA; // 10101010
    }

    // Set up pattern for char at index 3 (all 0x55)
    for (int i = 0; i < 8; i++) {
        charset.m_bitmap[24 + i] = 0x55; // 01010101
    }

    // Set up pattern for char at index 4 (specific pattern)
    uint8_t pattern4[8] = {0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0};
    for (int i = 0; i < 8; i++) {
        charset.m_bitmap[32 + i] = pattern4[i];
    }

    // Set up pattern for char at index 5 (different pattern)
    uint8_t pattern5[8] = {0x21, 0x43, 0x65, 0x87, 0xA9, 0xCB, 0xED, 0x0F};
    for (int i = 0; i < 8; i++) {
        charset.m_bitmap[40 + i] = pattern5[i];
    }

    SECTION("Distance between identical characters is zero") {
        Char c1(&charset, 0);
        Char c2(&charset, 0);

        REQUIRE(c1.distance(c2) == 0);
        REQUIRE(c2.distance(c1) == 0);
    }

    SECTION("Distance calculation is correct for one bit difference") {
        Char c1(&charset, 0); // All zeros
        Char c2(&charset, 1); // One bit set

        REQUIRE(c1.distance(c2) == 1);
        REQUIRE(c2.distance(c1) == 1);
    }

    SECTION("Distance calculation is correct for alternating patterns") {
        Char c1(&charset, 2); // All 0xAA (10101010...)
        Char c2(&charset, 3); // All 0x55 (01010101...)

        // All bits are different, so 8 bytes * 8 bits = 64 differences
        REQUIRE(c1.distance(c2) == 64);
        REQUIRE(c2.distance(c1) == 64);
    }

    SECTION("Distance calculation is correct for specific patterns") {
        Char c1(&charset, 4); // Pattern from pattern4
        Char c2(&charset, 5); // Pattern from pattern5

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
        Char c1(&charset, 0); // All zeros
        Char c2(&charset, 0); // All zeros (same)
        Char c3(&charset, 1); // One bit different

        REQUIRE(c1 == c2);     // Should be true (identical)
        REQUIRE_FALSE(c1 == c3); // Should be false (one bit different)
        REQUIRE_FALSE(c1 != c2); // Should be false (identical)
        REQUIRE(c1 != c3);     // Should be true (one bit different)
    }

    SECTION("Distance function matches direct hamming_distance_8bytes call") {
        Char c1(&charset, 4); // Pattern from pattern4
        Char c2(&charset, 5); // Pattern from pattern5

        // Direct call to the hamming distance function
        uint16_t direct_distance = hamming_distance_8bytes(
                &charset.m_bitmap[32], // pattern4 location
                &charset.m_bitmap[40]  // pattern5 location
        );

        // Should match the value from the Char class method
        REQUIRE(c1.distance(c2) == direct_distance);
    }
}