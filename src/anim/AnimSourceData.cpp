#include "AnimSourceData.h"
#include <typeinfo>

#ifdef __GNUC__  // GCC or Clang

#include <cxxabi.h>

#endif

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

uint16_t Char::useCount() const {
    return m_parentCharset->m_usageCount[m_index];
}

void Char::incUseCount() {
    m_parentCharset->m_usageCount[m_index] += 1;
}

std::string SourceChannel::getName() const {
    const std::type_info &info = typeid(*this);
#ifdef __GNUC__
    int status;
    char *demangled = abi::__cxa_demangle(info.name(), nullptr, nullptr, &status);
    if (demangled != nullptr) {
        std::string result(demangled);
        free(demangled);
        return result;
    }
#endif
    return info.name();
}