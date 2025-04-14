#include "Charset.h"

using namespace AnimTool;

uint8_t *Char::data() {
    return &m_parentCharset->m_bitmap[m_index * 8];
}

const uint8_t *Char::data() const {
    return &m_parentCharset->m_bitmap[m_index * 8];
}

void Char::clear() {
    uint8_t *ptr = data();
    for (int i = 0; i < 8; i++) {
        ptr[i] = 0;
    }
}

void Char::invert() {
    uint8_t *ptr = data();
    for (int i = 0; i < 8; i++) {
        ptr[i] = ~ptr[i];
    }
}
