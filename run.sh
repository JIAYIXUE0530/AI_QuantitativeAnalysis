#!/bin/bash
# 启动 TRAE AI 量化投资系统

cd "$(dirname "$0")"

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv .venv
fi

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
echo "检查依赖..."
pip install -q -r requirements.txt

# 检查 .env
if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 文件，请复制 .env.example 并填入 ANTHROPIC_API_KEY"
    cp .env.example .env
    echo "已创建 .env，请编辑后重新运行"
    exit 1
fi

# 启动 Streamlit
echo "启动 TRAE AI 量化投资系统..."
streamlit run ui/app.py --server.port 8501 --server.headless false
