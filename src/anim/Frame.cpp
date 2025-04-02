#include "Frame.h"

using namespace AnimTool::Anim;

uint8_t *Char::data() {
    return &parentCharset->bitmap[index * 8];
}

const uint8_t *Char::data() const {
    return &parentCharset->bitmap[index * 8];
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

uint16_t Char::useCount() const {
    return parentCharset->usage_count[index];
}

void Char::incUseCount() {
    parentCharset->usage_count[index] += 1;
}
