#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vercel优化版应用文件
负成本持仓策略管理系统
"""

import os
import sys
import sqlite3
import tempfile
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
import json

# Vercel环境配置
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'vercel-strategy-app-2025')

# Vercel临时文件系统配置
TEMP_DIR = '/tmp'
DB_PATH = os.path.join(TEMP_DIR, 'strategy.db')

class VercelStrategyDatabase:
    """Vercel环境下的数据库管理类"""
    
    def __init__(self):
        self.db_path = DB_PATH
        self.init_database()
    
    def init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建股票表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    current_price REAL NOT NULL,
                    target_shares INTEGER NOT NULL,
                    current_shares INTEGER DEFAULT 0,
                    average_cost REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建交易记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT NOT NULL,
                    trade_type TEXT NOT NULL,
                    shares INTEGER NOT NULL,
                    price REAL NOT NULL,
                    trade_date DATE NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (stock_code) REFERENCES stocks (code)
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"数据库初始化错误: {e}")
    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)

# 全局数据库实例
db = VercelStrategyDatabase()

@app.route('/')
def index():
    """首页"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT code, name, current_price, target_shares, current_shares, average_cost
            FROM stocks ORDER BY created_at DESC
        ''')
        stocks = cursor.fetchall()
        
        # 计算统计数据
        total_value = 0
        total_cost = 0
        total_profit = 0
        
        stock_data = []
        for stock in stocks:
            code, name, current_price, target_shares, current_shares, average_cost = stock
            current_value = current_shares * current_price
            total_cost_for_stock = current_shares * average_cost
            profit = current_value - total_cost_for_stock
            
            total_value += current_value
            total_cost += total_cost_for_stock
            total_profit += profit
            
            stock_data.append({
                'code': code,
                'name': name,
                'current_price': current_price,
                'target_shares': target_shares,
                'current_shares': current_shares,
                'average_cost': average_cost,
                'current_value': current_value,
                'profit': profit,
                'profit_rate': (profit / total_cost_for_stock * 100) if total_cost_for_stock > 0 else 0
            })
        
        conn.close()
        
        return render_template('index.html', 
                             stocks=stock_data,
                             total_value=total_value,
                             total_cost=total_cost,
                             total_profit=total_profit,
                             total_profit_rate=(total_profit / total_cost * 100) if total_cost > 0 else 0)
    
    except Exception as e:
        flash(f'数据加载错误: {str(e)}', 'error')
        return render_template('index.html', stocks=[], total_value=0, total_cost=0, total_profit=0, total_profit_rate=0)

@app.route('/add_stock', methods=['GET', 'POST'])
def add_stock():
    """添加股票"""
    if request.method == 'POST':
        try:
            code = request.form['code'].upper()
            name = request.form['name']
            current_price = float(request.form['current_price'])
            target_shares = int(request.form['target_shares'])
            current_shares = int(request.form.get('current_shares', 0))
            average_cost = float(request.form.get('average_cost', current_price))
            
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO stocks (code, name, current_price, target_shares, current_shares, average_cost)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (code, name, current_price, target_shares, current_shares, average_cost))
            
            conn.commit()
            conn.close()
            
            flash(f'股票 {code} 添加成功！', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            flash(f'添加失败: {str(e)}', 'error')
    
    return render_template('add_stock.html')

@app.route('/health')
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected' if os.path.exists(DB_PATH) else 'initializing'
    })

# Vercel serverless函数处理器
def handler(request):
    """Vercel请求处理器"""
    return app(request.environ, request.start_response)

# 确保在Vercel环境中正确初始化
if not os.path.exists(DB_PATH):
    db.init_database()

# 导出应用供Vercel使用
application = app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

