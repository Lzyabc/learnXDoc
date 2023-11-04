# TODO: 请根据示例，配置老师和学生的账号
users = {
    "teacher": {
        "name": "Teacher",
        "mail": " ",
        "username": "teacher",
        "name_py": "Teacher",
        "class": "1",
        "major": "计算机科学与技术",
        "role": "teacher",
        "password": "123456"
    },
    "test": {
        "name": "student",
        "mail": " ",
        "username": "student",
        "name_py": "Student",
        "class": "1",
        "major": "计算机科学与技术",
        "role": "student",
        "password": "123456"
    }
}


# 容器中的测试账号（仅供测试，生产环境请使用复杂密码！）
mysql = {
    "user": "root",
    "passwd": "test",
    "host": "localhost"
}

# 账号信息
redis = {
    "port": 6379,
    "host": "localhost"
}

mongo = {
    "user": "admin",
    "passwd": "123456",
    "host": "localhost",
    "port": "27017" 
}


nginx = {
    "front_port": "7002",
    "front_root": "/usr/share/nginx/html/",
    "server_port": "7002",
    "server_listen_port": "7001",
    "server_name": "",
    "config_path": "/etc/nginx/nginx.conf1",
    "nginx_user": "www-data",
    "ssl_str": "",
    "ssl": True,
    "ssl_cert": "",
    "ssl_key": ""
}

url = "https://localhost:8000"
did_ca_server="http://localhost:8003/"
