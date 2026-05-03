#pragma once

#include "Types.hpp"
#include <string>

class ConfigLoader {
public:
    static RiskConfig loadRiskConfig(const std::string& path);
};
