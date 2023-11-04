本文档介绍了learnX的部署方法。

1. 环境配置
- 配置前端：
  打开文件夹workspace/.env.production，修改VUE_APP_URL为后端服务URI, VUE_APP_FRONT_URL为前端URI。
  例如，前端URI是http://cs101.ucas.ac.cn:7001，后端URI是http://cs101.ucas.ac.cn:7002，则修改为：
```
    VUE_APP_URL='http://cs101.ucas.ac.cn:7002'
    VUE_APP_FRONT_URL='http://cs101.ucas.ac.cn:7001'
```

- 配置后端：
  打开文件夹workspace/config.py, 根据config.py中的TODO提示，设置需要创建的账号。

2. 启动服务
   learnX的服务分为前端和后端两部分，打包到了一个容器中。请使用以下命令启动容器（把PATH_TO_WORKSPACE修改为workspace文件夹地址）。后端服务会在7001端口启动，前端服务会在7002端口启动。
```
    docker run -it -v PATH_TO_WORKSPACE:/workspace -p 7001:7001 7002:7002 lucaszy/learnx:latest /init.sh
```

3. 发布到公网
    可以使用nginx或者apache等工具，将7001和7002端口映射到公网端口。具体请参考[nginx文档](https://nginx.org/en/docs/)或者[apache文档](https://httpd.apache.org/docs/)。
    