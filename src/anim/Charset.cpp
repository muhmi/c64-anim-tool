#include "Charset.h"

using namespace AnimTool;

const uint8_t BLANK_DATA[] = {0, 0, 0, 0, 0, 0, 0, 0};
const uint8_t FULL_DATA[] = {0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff};

Char Char::BLANK = Char(BLANK_DATA);
Char Char::FULL = Char(FULL_DATA);

Char::Char(const uint8_t *bitmap) { std::memcpy(m_bitmap, bitmap, 8); }

uint8_t *Char::data() { return m_bitmap; }

const uint8_t *Char::data() const { return m_bitmap; }

void Char::clear() { std::memset(m_bitmap, 0, 8); }

void Char::invert() {
    for (unsigned char &i : m_bitmap) {
        i = ~i;
    }
}

bool Char::isBlank() const {
    return std::ranges::all_of(m_bitmap, [](uint8_t v) { return v == 0; });
}

size_t Charset::hash() const {
    size_t hash_value = fnv1a_hash(m_sourceFilename);

    size_t bitmap_hash = 0;
    for (const auto &ch : m_characters) {
        bitmap_hash = bitmap_hash * 31 + ch.hash();
    }

    hash_value ^= bitmap_hash + 0x9e3779b9 + (hash_value << 6) + (hash_value >> 2);

    return hash_value;
}

bool Charset::operator==(const Charset &other) const {
    // First check if filenames match
    if (m_sourceFilename != other.m_sourceFilename) return false;

    // Then check if they have the same number of characters
    if (m_characters.size() != other.m_characters.size()) return false;

    // Finally check each character for equality
    for (size_t idx = 0; idx < m_characters.size(); ++idx) {
        if (m_characters[idx] != other.m_characters[idx]) return false;
    }
    return true;
}

bool Charset::operator!=(const Charset &other) const { return !(*this == other); }

uint8_t Charset::insert(const Char &character) {
    // Search for existing character
    auto it = std::find(m_characters.begin(), m_characters.end(), character);
    if (it != m_characters.end()) {
        return static_cast<uint8_t>(std::distance(m_characters.begin(), it));
    }

    // Add new character if not found
    uint8_t index = static_cast<uint8_t>(m_characters.size());
    m_characters.push_back(character);
    return index;
}

std::optional<uint8_t> Charset::indexOf(const Char &character) const {
    auto it = std::find(m_characters.begin(), m_characters.end(), character);
    if (it != m_characters.end()) {
        return static_cast<uint8_t>(std::distance(m_characters.begin(), it));
    }
    return {};
}

uint8_t Charset::closestChar(const Char &character) const {
    uint8_t best_idx = 0;
    uint16_t min_distance = std::numeric_limits<uint16_t>::max();

    for (size_t i = 0; i < m_characters.size(); i++) {
        uint16_t dist = character.distance(m_characters[i]);
        if (dist < min_distance) {
            min_distance = dist;
            best_idx = static_cast<uint8_t>(i);
        }
    }

    return best_idx;
}
