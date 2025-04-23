#pragma once

#include <functional>
#include <type_traits>
#include <utility>

namespace AnimTool {

class Defer {
   public:
    template <typename F, typename = std::enable_if_t<!std::is_same_v<std::decay_t<F>, Defer>>>
    explicit Defer(F &&func) : cleanup_func(std::forward<F>(func)) {}

    ~Defer() {
        if (cleanup_func) {
            cleanup_func();
        }
    }

    Defer(const Defer &) = delete;

    Defer &operator=(const Defer &) = delete;

    Defer(Defer &&other) noexcept : cleanup_func(std::move(other.cleanup_func)) {
        other.cleanup_func = std::function<void()>();
    }

    Defer &operator=(Defer &&other) noexcept {
        if (this != &other) {
            if (cleanup_func) {
                cleanup_func();
            }
            cleanup_func = std::move(other.cleanup_func);
            other.cleanup_func = std::function<void()>();
        }
        return *this;
    }

   private:
    std::function<void()> cleanup_func;
};

// Helper function
template <typename F>
Defer makeDefer(F &&func) {
    return Defer(std::forward<F>(func));
}
}  // namespace AnimTool