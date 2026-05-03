#pragma once

#include "Types.hpp"
#include <string>
#include <vector>

class MarketData {
public:
    static std::vector<Tick> loadTicksFromCsv(const std::string& path);
};
