#include "Charset.h"

using namespace AnimTool;

Char::Char(const uint8_t *bitmap, uint8_t idx) : m_index(idx) {
    std::memcpy(m_bitmap, bitmap, 8);
}

uint8_t *Char::data() {
    return m_bitmap;
}

const uint8_t *Char::data() const {
    return m_bitmap;
}

void Char::clear() {
    std::memset(m_bitmap, 0, 8);
}

void Char::invert() {
    for (int i = 0; i < 8; i++) {
        m_bitmap[i] = ~m_bitmap[i];
    }
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
    if (m_sourceFilename != other.m_sourceFilename)
        return false;

    // Then check if they have the same number of characters
    if (m_characters.size() != other.m_characters.size())
        return false;

    // Finally check each character for equality
    for (size_t idx = 0; idx < m_characters.size(); ++idx) {
        if (m_characters[idx] != other.m_characters[idx])
            return false;
    }
    return true;
}

bool Charset::operator!=(const Charset &other) const {
    return !(*this == other);
}

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