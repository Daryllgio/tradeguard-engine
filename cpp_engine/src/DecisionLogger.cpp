#include "DecisionLogger.hpp"
#include <fstream>
#include <stdexcept>

static std::string signalToString(SignalType signal) {
    switch (signal) {
        case SignalType::LONG: return "LONG";
        case SignalType::SHORT: return "SHORT";
        default: return "NONE";
    }
}

static std::string decisionToString(DecisionType decision) {
    return decision == DecisionType::ACCEPTED ? "ACCEPTED" : "REJECTED";
}

void DecisionLogger::writeDecisions(const std::string& path, const std::vector<TradeDecision>& decisions) {
    std::ofstream file(path);
    if (!file.is_open()) throw std::runtime_error("Could not write decisions file: " + path);

    file << "timestamp,decision,signal,reason,entry_price,stop_loss,take_profit,quantity,risk_dollars,notional_value\n";

    for (const auto& d : decisions) {
        file << d.timestamp << ","
             << decisionToString(d.decision) << ","
             << signalToString(d.signal) << ","
             << "\"" << d.reason << "\"" << ","
             << d.entryPrice << ","
             << d.stopLoss << ","
             << d.takeProfit << ","
             << d.quantity << ","
             << d.riskDollars << ","
             << d.notionalValue << "\n";
    }
}

void DecisionLogger::writeTrades(const std::string& path, const std::vector<TradeResult>& trades) {
    std::ofstream file(path);
    if (!file.is_open()) throw std::runtime_error("Could not write trades file: " + path);

    file << "timestamp,side,entry_price,exit_price,quantity,pnl,exit_reason\n";

    for (const auto& t : trades) {
        file << t.timestamp << ","
             << signalToString(t.side) << ","
             << t.entryPrice << ","
             << t.exitPrice << ","
             << t.quantity << ","
             << t.pnl << ","
             << t.exitReason << "\n";
    }
}

void DecisionLogger::writeEquityCurve(const std::string& path, const std::vector<double>& equityCurve) {
    std::ofstream file(path);
    if (!file.is_open()) throw std::runtime_error("Could not write equity curve file: " + path);

    file << "step,equity\n";

    for (size_t i = 0; i < equityCurve.size(); ++i) {
        file << i << "," << equityCurve[i] << "\n";
    }
}
