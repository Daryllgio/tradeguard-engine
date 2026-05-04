#include "ConfigLoader.hpp"
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>

static double extractNumber(const std::string& json, const std::string& key, double fallback) {
    std::string pattern = "\"" + key + "\"";
    size_t keyPos = json.find(pattern);

    if (keyPos == std::string::npos) {
        return fallback;
    }

    size_t colonPos = json.find(':', keyPos);
    if (colonPos == std::string::npos) {
        return fallback;
    }

    size_t valueStart = json.find_first_of("-0123456789.", colonPos);
    if (valueStart == std::string::npos) {
        return fallback;
    }

    size_t valueEnd = json.find_first_not_of("0123456789.-", valueStart);
    std::string value = json.substr(valueStart, valueEnd - valueStart);

    return std::stod(value);
}

RiskConfig ConfigLoader::loadRiskConfig(const std::string& path) {
    std::ifstream file(path);

    if (!file.is_open()) {
        throw std::runtime_error("Could not open risk config file: " + path);
    }

    std::stringstream buffer;
    buffer << file.rdbuf();
    std::string json = buffer.str();

    RiskConfig config;
    config.accountEquity = extractNumber(json, "account_equity", config.accountEquity);
    config.maxRiskPerTradePct = extractNumber(json, "max_risk_per_trade_pct", config.maxRiskPerTradePct);
    config.maxDailyLossPct = extractNumber(json, "max_daily_loss_pct", config.maxDailyLossPct);
    config.maxPositionValuePct = extractNumber(json, "max_position_value_pct", config.maxPositionValuePct);
    config.maxSymbolExposurePct = extractNumber(json, "max_symbol_exposure_pct", config.maxSymbolExposurePct);
    config.maxPortfolioExposurePct = extractNumber(json, "max_portfolio_exposure_pct", config.maxPortfolioExposurePct);
    config.stopLossPct = extractNumber(json, "stop_loss_pct", config.stopLossPct);
    config.takeProfitPct = extractNumber(json, "take_profit_pct", config.takeProfitPct);
    config.slippagePct = extractNumber(json, "slippage_pct", config.slippagePct);
    config.commissionPerTrade = extractNumber(json, "commission_per_trade", config.commissionPerTrade);

    return config;
}
