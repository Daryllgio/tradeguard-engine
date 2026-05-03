cmake_minimum_required(VERSION 3.20)

project(TradeGuardEngine VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

include_directories(include)

set(TRADEGUARD_SOURCES
    src/MarketData.cpp
    src/CandleBuilder.cpp
    src/SignalEngine.cpp
    src/RiskEngine.cpp
    src/Backtester.cpp
    src/DecisionLogger.cpp
    src/PerformanceMetrics.cpp
    src/ConfigLoader.cpp
    src/Benchmark.cpp
)

add_executable(tradeguard
    src/main.cpp
    ${TRADEGUARD_SOURCES}
)

add_executable(tradeguard_tests
    tests/test_engine.cpp
    src/SignalEngine.cpp
    src/RiskEngine.cpp
    src/CandleBuilder.cpp
    src/ConfigLoader.cpp
)

target_compile_options(tradeguard PRIVATE -Wall -Wextra -Wpedantic)
target_compile_options(tradeguard_tests PRIVATE -Wall -Wextra -Wpedantic)

enable_testing()
add_test(NAME TradeGuardEngineTests COMMAND tradeguard_tests)
