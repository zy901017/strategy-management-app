#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vercel API入口文件
负成本持仓策略管理系统
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 导入Flask应用
from app import app

# Vercel serverless函数处理器
def handler(request):
    """处理Vercel serverless请求"""
    return app(request.environ, request.start_response)

# 导出应用实例供Vercel使用
application = app

if __name__ == "__main__":
    app.run(debug=True)

