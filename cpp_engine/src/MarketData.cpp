#include "MarketData.hpp"
#include <fstream>
#include <sstream>
#include <stdexcept>

std::vector<Tick> MarketData::loadTicksFromCsv(const std::string& path) {
    std::ifstream file(path);
    if (!file.is_open()) {
        throw std::runtime_error("Could not open market data file: " + path);
    }

    std::vector<Tick> ticks;
    std::string line;
    std::getline(file, line);

    while (std::getline(file, line)) {
        std::stringstream ss(line);
        std::string timestamp, symbol, price, volume;

        std::getline(ss, timestamp, ',');
        std::getline(ss, symbol, ',');
        std::getline(ss, price, ',');
        std::getline(ss, volume, ',');

        if (timestamp.empty() || symbol.empty() || price.empty() || volume.empty()) {
            continue;
        }

        ticks.push_back(Tick{
            timestamp,
            symbol,
            std::stod(price),
            std::stod(volume)
        });
    }

    return ticks;
}
