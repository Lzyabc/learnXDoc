请在本地安装python3和[docker](https://www.docker.com/)

## 1. 创建 virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```
## 2. 安装 requirements.txt
```bash
pip install -r requirements.txt
```
## 3. 生成容器密码
其中num为生成的容器数量，file为生成的配置文件，port为容器的对外统一访问端口
```bash
python generate.py --num 30 --file config/create_students.json --port 8001
```

## 4. 根据生成的配置创建容器
```bash
python run.py -i config/create_students.json -o config/create_students_status.json -c create
# 通过docker ps查看容器状态，如果创建成功，则所有容器状态为up
docker ps
```

config文件夹中nginx.conf 为nginx配置映射，accounts.json列出了每一个容器的路径和密码。