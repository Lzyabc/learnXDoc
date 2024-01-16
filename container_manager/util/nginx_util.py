import os

def get_personal_artifact_config(path, port):
    return "        location /" + path + "/personal_artifact/ {" + """
                proxy_pass http://localhost:{port}/;""".format(port=port) + """
                proxy_set_header Host $host;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection upgrade;
                proxy_set_header Accept-Encoding gzip;
        }\n
"""
def get_vs_path_config(path, port):
    return "        location /" + path + "/ {" + """
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
