#include "AnimSourceData.h"
#include <typeinfo>

#ifdef __GNUC__  // GCC or Clang

#include <cxxabi.h>

#endif

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