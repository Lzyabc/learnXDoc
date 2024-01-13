import os

header_config = """
user www-data;
worker_processes auto;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {
	worker_connections 768;
	# multi_accept on;
}

http {

	##
	# Basic Settings
	##

	sendfile on;
	tcp_nopush on;
	tcp_nodelay on;
	keepalive_timeout 65;
	types_hash_max_size 2048;
	# server_tokens off;

	# server_names_hash_bucket_size 64;
	# server_name_in_redirect off;

	include /etc/nginx/mime.types;
	default_type application/octet-stream;

	##
	# SSL Settings
	##

	ssl_protocols TLSv1 TLSv1.1 TLSv1.2 TLSv1.3; # Dropping SSLv3, ref: POODLE
	ssl_prefer_server_ciphers on;

	##
	# Logging Settings
	##

	access_log /var/log/nginx/access.log;
	error_log /var/log/nginx/error.log;

	##
	# Gzip Settings
	##

	gzip on;

	include /etc/nginx/conf.d/*.conf;
	include /etc/nginx/sites-enabled/*;
    server {
        listen       7001 ssl;
        listen       [::]:7001 ssl;"""
server_config = """
        server_name  {domain}.things.ac.cn;
	    ssl_certificate "/etc/letsencrypt/live/{domain}.things.ac.cn/fullchain.pem";
        ssl_certificate_key "/etc/letsencrypt/live/{domain}.things.ac.cn/privkey.pem";
        ssl_session_cache shared:SSL:1m;
        ssl_session_timeout  10m;
"""

include_config = """
        include /etc/nginx/default.d/*.conf;
	}
}
"""

def get_personal_artifact_config(path, port):
    return "\t\tlocation /" + path + "/personal_artifact/ {" + """
                proxy_pass http://localhost:{port}/;""".format(port=port) + """
                proxy_set_header Host $host;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection upgrade;
                proxy_set_header Accept-Encoding gzip;
        }\n
"""
def get_vs_path_config(path, port):
    return "\t\tlocation /" + path + "/ {" + """
                proxy_pass http://localhost:{port}/;""".format(port=port) + """
                proxy_set_header Host $host;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection upgrade;
                proxy_set_header Accept-Encoding gzip;
        }\n
"""
def write_nginx_config(env, info_list):
    print(info_list)
    with open(env["nginx"], "w") as f:
        for name in info_list:
            f.write(get_vs_path_config(name, info_list[name]["port_map"]["8080/tcp"]))
            f.write(get_personal_artifact_config(name, info_list[name]["port_map"]["8081/tcp"]))
    return True
