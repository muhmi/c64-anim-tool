#include <string>

namespace AnimTool {
    class Charset;

    class CharsetReader {
    public:
        /**
         * Read a charset from .bin or .64c file, throws exception on errors
         *
         * @param charset_filename Path to the charset file to be loaded
         * @return The loaded Charset object
         * @throws std::runtime_error If the file cannot be opened
         * @throws std::runtime_error If the file format is invalid
         * @throws std::runtime_error If seeking within the file fails
         * @throws std::runtime_error If reading from the file fails
         * @throws std::invalid_argument If the file extension is not supported
         * */
        [[nodiscard]] static Charset readCharset(const std::string &filename);
    };
}