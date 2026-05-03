#pragma once

#include "Types.hpp"
#include "PerformanceMetrics.hpp"
#include <string>
#include <vector>

class DecisionLogger {
public:
    static void writeDecisions(const std::string& path, const std::vector<TradeDecision>& decisions);
    static void writeTrades(const std::string& path, const std::vector<TradeResult>& trades);
    static void writeEquityCurve(const std::string& path, const std::vector<double>& equityCurve);
    static void writeSummaryJson(const std::string& path, const PerformanceMetrics& metrics);
};
