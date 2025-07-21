#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
负成本持仓策略Web应用 - 修复版
修复持仓数量计算错误
"""

import os
import sqlite3
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import json
import math

app = Flask(__name__)
app.secret_key = 'strategy_management_2025_fixed'

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'strategy.db')

class StrategyDatabase:
    """策略数据库管理类"""
    
    def __init__(self):
        self.init_database()
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 创建股票基本信息表（修复字段顺序）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                market TEXT NOT NULL,
                target_shares INTEGER DEFAULT 100,
                initial_investment REAL DEFAULT 0,
                current_shares INTEGER DEFAULT 0,
                avg_cost REAL DEFAULT 0,
                total_fees REAL DEFAULT 0,
                current_price REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建交易记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                trade_date DATE NOT NULL,
                trade_type TEXT NOT NULL,
                shares INTEGER NOT NULL,
                price REAL NOT NULL,
                fees REAL DEFAULT 5,
                fund_source TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stock_code) REFERENCES stocks (code)
            )
        """)
        
        # 创建资金管理表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fund_management (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                additional_funds REAL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 插入默认资金管理记录
        cursor.execute('SELECT COUNT(*) FROM fund_management')
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO fund_management (additional_funds) VALUES (0)')
        
        conn.commit()
        conn.close()
    
    def get_stocks(self):
        """获取所有股票信息"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM stocks ORDER BY code')
        stocks = cursor.fetchall()
        conn.close()
        return stocks
    
    def get_stock(self, code):
        """获取单个股票信息"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM stocks WHERE code = ?', (code,))
        stock = cursor.fetchone()
        conn.close()
        return stock
    
    def add_stock(self, code, name, market, target_shares=100, initial_investment=0, 
                  current_shares=0, avg_cost=0, total_fees=0, current_price=0):
        """添加新股票"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO stocks (code, name, market, target_shares, initial_investment, 
                                  current_shares, avg_cost, total_fees, current_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (code, name, market, target_shares, initial_investment, 
                  current_shares, avg_cost, total_fees, current_price))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def update_stock(self, code, **kwargs):
        """更新股票信息"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [code]
        
        cursor.execute(f'UPDATE stocks SET {set_clause} WHERE code = ?', values)
        conn.commit()
        conn.close()
    
    def delete_stock(self, code):
        """删除股票"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM trades WHERE stock_code = ?', (code,))
        cursor.execute('DELETE FROM stocks WHERE code = ?', (code,))
        conn.commit()
        conn.close()
    
    def get_trades(self, stock_code=None):
        """获取交易记录"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if stock_code:
            cursor.execute("""
                SELECT * FROM trades WHERE stock_code = ? 
                ORDER BY trade_date DESC, created_at DESC
            """, (stock_code,))
        else:
            cursor.execute('SELECT * FROM trades ORDER BY trade_date DESC, created_at DESC')
        
        trades = cursor.fetchall()
        conn.close()
        return trades
    
    def add_trade(self, stock_code, trade_date, trade_type, shares, price, fees=5, fund_source='', notes=''):
        """添加交易记录"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO trades (stock_code, trade_date, trade_type, shares, price, fees, fund_source, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (stock_code, trade_date, trade_type, shares, price, fees, fund_source, notes))
        conn.commit()
        conn.close()
    
    def delete_trade(self, trade_id):
        """删除交易记录"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM trades WHERE id = ?', (trade_id,))
        conn.commit()
        conn.close()
    
    def get_fund_management(self):
        """获取资金管理信息"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM fund_management ORDER BY updated_at DESC LIMIT 1')
        fund = cursor.fetchone()
        conn.close()
        return fund
    
    def update_additional_funds(self, amount):
        """更新额外资金"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE fund_management SET additional_funds = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = (SELECT id FROM fund_management ORDER BY updated_at DESC LIMIT 1)
        """, (amount,))
        conn.commit()
        conn.close()

class StrategyCalculator:
    """策略计算类 - 修复版"""
    
    def __init__(self, db):
        self.db = db
    
    def calculate_stock_summary(self, stock_code):
        """计算单个股票的汇总信息 - 修复版"""
        stock = self.db.get_stock(stock_code)
        trades = self.db.get_trades(stock_code)
        
        if not stock:
            return None
        
        # 从数据库获取初始状态（修复字段索引）
        initial_shares = stock[6]  # current_shares 字段
        initial_avg_cost = stock[7]  # avg_cost 字段
        initial_total_fees = stock[8]  # total_fees 字段
        
        print(f"🔍 调试信息 - {stock_code}:")
        print(f"   数据库记录: {stock}")
        print(f"   初始持仓: {initial_shares}")
        print(f"   平均成本: {initial_avg_cost}")
        print(f"   总费用: {initial_total_fees}")
        
        # 计算交易后的状态
        current_shares = initial_shares
        total_profit = 0
        band_profit = 0
        total_cost = initial_shares * initial_avg_cost if initial_shares > 0 else 0
        total_fees = initial_total_fees
        buy_shares = initial_shares
        weighted_cost = initial_shares * initial_avg_cost if initial_shares > 0 else 0
        
        # 处理交易记录
        for trade in trades:
            trade_amount = trade[5] * trade[4]  # price * shares
            net_amount = trade_amount + trade[6] if trade[3] == '买入' else trade_amount - trade[6]
            total_fees += trade[6]
            
            if trade[3] == '买入':
                current_shares += trade[4]
                buy_shares += trade[4]
                total_cost += net_amount
                weighted_cost += trade[5] * trade[4]
                total_profit -= net_amount
            else:  # 卖出
                current_shares -= trade[4]
                sell_profit = net_amount - (trade[4] * (weighted_cost / max(buy_shares, 1)))
                total_profit += sell_profit
                if trade[7] == '波段操作':
                    band_profit += sell_profit
        
        avg_cost = weighted_cost / max(buy_shares, 1) if buy_shares > 0 else initial_avg_cost
        
        result = {
            'current_shares': current_shares,
            'total_profit': total_profit,
            'band_profit': max(band_profit, 0),
            'avg_cost': avg_cost,
            'total_cost': total_cost,
            'total_fees': total_fees
        }
        
        print(f"   计算结果: {result}")
        
        return result
    
    def calculate_portfolio_summary(self):
        """计算投资组合汇总 - 修复版"""
        stocks = self.db.get_stocks()
        fund_info = self.db.get_fund_management()
        
        total_band_profit = 0
        portfolio_data = []
        
        for stock in stocks:
            summary = self.calculate_stock_summary(stock[1])  # stock[1] is code
            if not summary:
                continue
                
            current_value = summary['current_shares'] * stock[9]  # current_price 字段索引修正
            
            total_band_profit += summary['band_profit']
            
            # 计算负成本状态
            negative_cost_status = "未达成"
            initial_investment = stock[5]  # initial_investment 字段
            if summary['band_profit'] >= initial_investment and initial_investment > 0:
                negative_cost_status = "已达成"
            elif summary['band_profit'] > 0 and initial_investment > 0:
                progress = (summary['band_profit'] / initial_investment) * 100
                negative_cost_status = f"进度 {progress:.1f}%"
            
            portfolio_data.append({
                'code': stock[1],
                'name': stock[2],
                'market': stock[3],
                'current_shares': summary['current_shares'],  # 使用计算后的持仓数量
                'target_shares': stock[4],
                'initial_investment': initial_investment,
                'avg_cost': summary['avg_cost'],
                'total_fees': summary['total_fees'],
                'current_price': stock[9],  # current_price 字段
                'current_value': current_value,
                'total_profit': summary['total_profit'],
                'band_profit': summary['band_profit'],
                'progress': summary['current_shares'] / stock[4] if stock[4] > 0 else 0,
                'negative_cost_status': negative_cost_status
            })
        
        additional_funds = fund_info[1] if fund_info else 0
        total_available_funds = total_band_profit + additional_funds
        
        return {
            'portfolio': portfolio_data,
            'total_band_profit': total_band_profit,
            'additional_funds': additional_funds,
            'total_available_funds': total_available_funds
        }
    
    def generate_strategy_suggestions(self):
        """生成增强版策略建议"""
        portfolio = self.calculate_portfolio_summary()
        suggestions = []
        
        for stock in portfolio['portfolio']:
            code = stock['code']
            name = stock['name']
            current_price = stock['current_price']
            avg_cost = stock['avg_cost']
            current_shares = stock['current_shares']
            target_shares = stock['target_shares']
            band_profit = stock['band_profit']
            initial_investment = stock['initial_investment']
            
            # 计算关键指标
            shares_needed = max(0, target_shares - current_shares)
            price_vs_cost = (current_price - avg_cost) / avg_cost if avg_cost > 0 else 0
            progress = current_shares / target_shares if target_shares > 0 else 0
            
            # 价格分析
            if price_vs_cost > 0.15:
                price_analysis = "价格偏高，建议等待回调"
                price_color = "danger"
                price_advice = f"当前价格比成本高{price_vs_cost*100:.1f}%，建议等待回调至${avg_cost*1.05:.2f}以下"
            elif price_vs_cost > 0.05:
                price_analysis = "价格适中偏高"
                price_color = "warning"
                price_advice = f"价格略高于成本{price_vs_cost*100:.1f}%，可小量买入或等待更好机会"
            elif price_vs_cost > -0.05:
                price_analysis = "价格合理"
                price_color = "info"
                price_advice = "价格接近成本价，是较好的买入时机"
            elif price_vs_cost > -0.15:
                price_analysis = "价格偏低，抄底机会"
                price_color = "success"
                price_advice = f"价格低于成本{abs(price_vs_cost)*100:.1f}%，建议积极买入"
            else:
                price_analysis = "价格严重偏低，绝佳机会"
                price_color = "success"
                price_advice = f"价格大幅低于成本{abs(price_vs_cost)*100:.1f}%，强烈建议大量买入"
            
            # 增持策略建议
            if shares_needed == 0:
                holding_advice = "✅ 已达到目标持仓，建议开始波段操作获取负成本"
                holding_priority = "低"
                holding_action = "开始波段操作，每次上涨10%时卖出20%持仓"
            elif shares_needed <= 10:
                holding_advice = f"🎯 接近目标！还需{shares_needed}股"
                holding_priority = "高"
                holding_action = f"建议一次性买入{shares_needed}股完成目标"
            elif shares_needed <= 30:
                holding_advice = f"📈 中期目标，还需{shares_needed}股"
                holding_priority = "中"
                holding_action = f"建议分3批买入，每批{shares_needed//3}股，间隔1-2周"
            else:
                holding_advice = f"📊 长期目标，还需{shares_needed}股"
                holding_priority = "中"
                holding_action = f"建议分6批买入，每批{shares_needed//6}股，每月1批"
            
            # 波段操作建议
            if current_shares >= 10:
                if price_vs_cost > 0.1:
                    sell_shares = min(current_shares//3, 8)
                    expected_profit = sell_shares * current_price * 0.1
                    band_advice = f"💰 建议卖出{sell_shares}股进行波段操作"
                    band_detail = f"目标卖价: ${current_price*1.05:.2f}, 回购价: ${current_price*0.95:.2f}"
                    band_profit_estimate = f"预期单次波段盈利: ${expected_profit:.2f}"
                elif price_vs_cost < -0.1:
                    band_advice = "⏰ 价格偏低，暂不卖出，等待反弹至成本价以上"
                    band_detail = f"等待价格回升至${avg_cost*1.1:.2f}以上再考虑波段"
                    band_profit_estimate = "当前不适合波段操作"
                else:
                    sell_shares = min(current_shares//4, 5)
                    expected_profit = sell_shares * current_price * 0.08
                    band_advice = f"📊 可考虑小量波段，卖出{sell_shares}股"
                    band_detail = f"保守目标: 上涨8%时卖出，下跌8%时买回"
                    band_profit_estimate = f"预期盈利: ${expected_profit:.2f}"
            else:
                band_advice = "📈 持仓较少，建议先增持至20股以上再波段"
                band_detail = "小持仓波段操作效果有限，建议先积累更多股份"
                band_profit_estimate = "暂不适合波段操作"
            
            # 资金分配建议
            funds_needed = shares_needed * current_price * 1.02
            available_funds = portfolio['total_available_funds']
            
            if available_funds > funds_needed * 1.5:
                fund_advice = "💰 资金充足，可立即完成增持目标"
                fund_strategy = "建议一次性投入完成目标，剩余资金用于其他股票"
            elif available_funds > funds_needed:
                fund_advice = "💰 资金基本够用，可完成增持"
                fund_strategy = "建议分2-3批投入，保留部分资金应对机会"
            elif available_funds > funds_needed * 0.5:
                fund_advice = "⚖️ 资金有限，建议分批投入"
                fund_strategy = "先投入一半资金，等待波段盈利后继续"
            else:
                fund_advice = "⏳ 资金不足，需要更多波段盈利"
                fund_strategy = "专注波段操作获取更多资金，暂缓大量增持"
            
            # 负成本进度分析
            negative_cost_progress = (band_profit / initial_investment * 100) if initial_investment > 0 else 0
            remaining_profit_needed = max(0, initial_investment - band_profit)
            
            if negative_cost_progress >= 100:
                negative_cost_advice = "🎉 恭喜！已实现负成本持仓"
                negative_cost_detail = "现在的持仓完全是用盈利获得的，可以享受纯利润增长"
                negative_cost_color = "success"
            elif negative_cost_progress >= 80:
                negative_cost_advice = f"🚀 接近负成本！进度{negative_cost_progress:.1f}%"
                negative_cost_detail = f"还需${remaining_profit_needed:.2f}波段盈利即可实现负成本"
                negative_cost_color = "warning"
            elif negative_cost_progress >= 50:
                negative_cost_advice = f"📈 负成本进度{negative_cost_progress:.1f}%"
                negative_cost_detail = f"已完成一半目标，继续波段操作，还需${remaining_profit_needed:.2f}"
                negative_cost_color = "info"
            elif negative_cost_progress > 0:
                negative_cost_advice = f"🌱 已开始盈利，进度{negative_cost_progress:.1f}%"
                negative_cost_detail = f"良好开端！继续波段操作，目标${remaining_profit_needed:.2f}盈利"
                negative_cost_color = "info"
            else:
                negative_cost_advice = "📊 尚未开始负成本策略"
                negative_cost_detail = f"建议开始波段操作，目标获得${initial_investment:.2f}盈利"
                negative_cost_color = "secondary"
            
            # 风险评估
            volatility_risk = "高" if abs(price_vs_cost) > 0.2 else "中" if abs(price_vs_cost) > 0.1 else "低"
            position_risk = "高" if progress > 0.8 else "中" if progress > 0.4 else "低"
            
            # 时间预测
            if shares_needed > 0 and available_funds > 0:
                monthly_investment = min(available_funds / 6, shares_needed * current_price / 3)
                months_needed = max(1, (shares_needed * current_price) / monthly_investment)
                time_prediction = f"预计{months_needed:.0f}个月完成增持目标"
            else:
                time_prediction = "需要更多资金支持"
            
            # 具体操作步骤
            action_steps = []
            
            # 步骤1：价格判断
            if price_vs_cost < -0.1:
                action_steps.append("🎯 立即买入：价格偏低，绝佳机会")
            elif price_vs_cost > 0.1:
                action_steps.append("⏰ 等待回调：价格偏高，耐心等待")
            else:
                action_steps.append("📊 适量买入：价格合理，可以操作")
            
            # 步骤2：增持策略
            if shares_needed > 0:
                if shares_needed <= 10:
                    action_steps.append(f"🎯 完成增持：一次性买入{shares_needed}股")
                else:
                    action_steps.append(f"📈 分批增持：每次买入{min(10, shares_needed//3)}股")
            else:
                action_steps.append("✅ 开始波段：已达目标，专注波段操作")
            
            # 步骤3：波段操作
            if current_shares >= 10:
                action_steps.append("💰 波段获利：上涨10%时卖出部分股份")
                action_steps.append("🔄 循环操作：下跌时用盈利买回更多")
            else:
                action_steps.append("📈 积累股份：先增持至20股以上")
            
            # 步骤4：负成本目标
            if negative_cost_progress < 100:
                action_steps.append(f"🎯 负成本目标：还需${remaining_profit_needed:.0f}波段盈利")
            else:
                action_steps.append("🎉 享受收益：已实现负成本，纯利润增长")
            
            suggestions.append({
                'code': code,
                'name': name,
                'current_price': current_price,
                'avg_cost': avg_cost,
                'price_vs_cost_pct': price_vs_cost * 100,
                'price_analysis': price_analysis,
                'price_color': price_color,
                'price_advice': price_advice,
                'current_shares': current_shares,
                'target_shares': target_shares,
                'shares_needed': shares_needed,
                'progress_pct': progress * 100,
                'holding_advice': holding_advice,
                'holding_priority': holding_priority,
                'holding_action': holding_action,
                'band_advice': band_advice,
                'band_detail': band_detail,
                'band_profit_estimate': band_profit_estimate,
                'fund_advice': fund_advice,
                'fund_strategy': fund_strategy,
                'funds_needed': funds_needed,
                'negative_cost_advice': negative_cost_advice,
                'negative_cost_detail': negative_cost_detail,
                'negative_cost_color': negative_cost_color,
                'negative_cost_progress': negative_cost_progress,
                'time_prediction': time_prediction,
                'action_steps': action_steps,
                'volatility_risk': volatility_risk,
                'position_risk': position_risk,
                'band_profit': band_profit,
                'initial_investment': initial_investment
            })
        
        return suggestions