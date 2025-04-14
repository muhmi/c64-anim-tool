#include "AnimSourceData.h"
#include <typeinfo>

#ifdef __GNUC__  // GCC or Clang

#include <cxxabi.h>

#endif

using namespace AnimTool;

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