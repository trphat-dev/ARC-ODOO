/** @odoo-module */

import { registry } from "@web/core/registry";
import { TechnicalChartWidget } from "./technical_chart_widget";

// Register as client action
registry.category("actions").add("ai_trading_assistant.technical_chart_action", TechnicalChartWidget);

