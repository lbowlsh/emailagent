# 使用 Python 3.9 slim 作为基础镜像
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 设置工作目录
WORKDIR /code

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

# 添加非root用户
RUN useradd -m myuser
USER myuser


# 复制 requirements.txt 并安装依赖项
COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt -v

# 复制项目文件
COPY . /code/

# 暴露端口 5000
EXPOSE 5000

# 运行 Flask 应用
CMD ["python", "main.py"]

# CMD ["tail", "-f", "/dev/null"]