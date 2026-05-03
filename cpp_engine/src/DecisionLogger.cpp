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

static std::string reasonCodeToString(DecisionReasonCode code) {
    switch (code) {
        case DecisionReasonCode::TRADE_ACCEPTED: return "TRADE_ACCEPTED";
        case DecisionReasonCode::NO_SIGNAL: return "NO_SIGNAL";
        case DecisionReasonCode::MAX_DAILY_LOSS: return "MAX_DAILY_LOSS";
        case DecisionReasonCode::INVALID_STOP_DISTANCE: return "INVALID_STOP_DISTANCE";
        case DecisionReasonCode::POSITION_TOO_SMALL: return "POSITION_TOO_SMALL";
        case DecisionReasonCode::SYMBOL_EXPOSURE_LIMIT: return "SYMBOL_EXPOSURE_LIMIT";
        case DecisionReasonCode::PORTFOLIO_EXPOSURE_LIMIT: return "PORTFOLIO_EXPOSURE_LIMIT";
        default: return "UNKNOWN";
    }
}

void DecisionLogger::writeDecisions(const std::string& path, const std::vector<TradeDecision>& decisions) {
    std::ofstream file(path);
    if (!file.is_open()) throw std::runtime_error("Could not write decisions file: " + path);

    file << "timestamp,symbol,decision,reason_code,signal,reason,entry_price,stop_loss,take_profit,quantity,risk_dollars,notional_value\n";

    for (const auto& d : decisions) {
        file << d.timestamp << ","
             << d.symbol << ","
             << decisionToString(d.decision) << ","
             << reasonCodeToString(d.reasonCode) << ","
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

    file << "timestamp,symbol,side,entry_price,exit_price,quantity,pnl,exit_reason,exit_index\n";

    for (const auto& t : trades) {
        file << t.timestamp << ","
             << t.symbol << ","
             << signalToString(t.side) << ","
             << t.entryPrice << ","
             << t.exitPrice << ","
             << t.quantity << ","
             << t.pnl << ","
             << t.exitReason << ","
             << t.exitIndex << "\n";
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

void DecisionLogger::writeSummaryJson(const std::string& path, const PerformanceMetrics& metrics) {
    std::ofstream file(path);
    if (!file.is_open()) throw std::runtime_error("Could not write summary JSON file: " + path);

    file << "{\n";
    file << "  \"total_decisions\": " << metrics.totalDecisions << ",\n";
    file << "  \"accepted_trades\": " << metrics.acceptedTrades << ",\n";
    file << "  \"rejected_setups\": " << metrics.rejectedSetups << ",\n";
    file << "  \"executed_trades\": " << metrics.executedTrades << ",\n";
    file << "  \"ending_equity\": " << metrics.endingEquity << ",\n";
    file << "  \"total_pnl\": " << metrics.totalPnl << ",\n";
    file << "  \"win_rate\": " << metrics.winRate << ",\n";
    file << "  \"average_pnl\": " << metrics.averagePnl << ",\n";
    file << "  \"best_trade\": " << metrics.bestTrade << ",\n";
    file << "  \"worst_trade\": " << metrics.worstTrade << ",\n";
    file << "  \"max_drawdown\": " << metrics.maxDrawdown << "\n";
    file << "}\n";
}
