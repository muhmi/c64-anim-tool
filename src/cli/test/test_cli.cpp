#include <catch2/catch_test_macros.hpp>
#include <CLI/CLI.hpp>
/*
// Simple CLI parsing tests
TEST_CASE("CLI parsing", "[cli]") {
    CLI::App app{"Test App"};

    std::string input_file;
    std::string output_file;
    bool verbose = false;
    int quality = 100;

    app.add_option("-i,--input", input_file, "Input file");
    app.add_option("-o,--output", output_file, "Output file");
    app.add_flag("-v,--verbose", verbose, "Enable verbose output")
            ->
                    check(CLI::Range(1, 100)
            );

    SECTION("Basic options parsing") {
        std::vector<std::string> args = {
                "program",
                "-i", "input.gif",
                "-o", "output.gif",
                "-v",
                "-q", "85"
        };

        std::vector<char *> argv;
        argv.reserve(args.size());
for (
            auto &arg
                : args) {
            argv.push_back(const_cast
                                   <char *>(arg
                            .

                                    c_str()

                           ));
        }

        app.parse(static_cast
                          <int>(argv
                        .

                                size()

                  ), argv.

                data()

        );

        REQUIRE(input_file
                == "input.gif");
        REQUIRE(output_file
                == "output.gif");
        REQUIRE(verbose
                == true);
        REQUIRE(quality
                == 85);
    }

    SECTION("Long option names") {
        std::vector<std::string> args = {
                "program",
                "--input", "input.gif",
                "--output", "output.gif",
                "--verbose",
                "--quality", "50"
        };

        std::vector<char *> argv;
        argv.reserve(args.size());
for (
            auto &arg
                : args) {
            argv.push_back(const_cast
                                   <char *>(arg
                            .

                                    c_str()

                           ));
        }

        app.parse(static_cast
                          <int>(argv
                        .

                                size()

                  ), argv.

                data()

        );

        REQUIRE(input_file
                == "input.gif");
        REQUIRE(output_file
                == "output.gif");
        REQUIRE(verbose
                == true);
        REQUIRE(quality
                == 50);
    }

    SECTION("Quality range validation") {
        std::vector<std::string> args = {
                "program",
                "-i", "input.gif",
                "-q", "101"  // Out of range
        };

        std::vector<char *> argv(args.size());
        for (
            auto &arg
                : args) {
            argv.push_back(const_cast
                                   <char *>(arg
                            .

                                    c_str()

                           ));
        }

        REQUIRE_THROWS(app
                               .parse(static_cast
                                              <int>(argv
                                               .

                                                       size()

                                      ), argv.

                                       data()

                               ));
    }
}*/