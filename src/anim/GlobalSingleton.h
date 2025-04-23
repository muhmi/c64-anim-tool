#pragma once

#include <stdexcept>

namespace AnimTool {

    /**
     * A base class for creating managed global singletons.
     * The singleton instance only exists while its owning unique_ptr exists.
     */
    template <typename T>
    class GlobalSingleton {
       private:
        static T* s_pInstance;

       protected:
        GlobalSingleton();

        ~GlobalSingleton();

       public:
        // Non-copyable and non-movable
        GlobalSingleton(const GlobalSingleton&) = delete;
        GlobalSingleton& operator=(const GlobalSingleton&) = delete;
        GlobalSingleton(GlobalSingleton&&) = delete;
        GlobalSingleton& operator=(GlobalSingleton&&) = delete;

        // Get the singleton instance
        static T* getInstance() { return s_pInstance; }
    };

    template <typename T>
    T* GlobalSingleton<T>::s_pInstance = nullptr;

    template <typename T>
    GlobalSingleton<T>::~GlobalSingleton() {
        if (s_pInstance == static_cast<T*>(this)) {
            s_pInstance = nullptr;
        }
    }
    template <typename T>
    GlobalSingleton<T>::GlobalSingleton() {
        // Ensure there isn't already an instance
        if (s_pInstance != nullptr) {
            throw std::runtime_error("Singleton instance already exists");
        }
        s_pInstance = static_cast<T*>(this);
    }

}  // namespace AnimTool