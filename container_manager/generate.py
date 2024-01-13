import random
import string
import json
import os
import argparse

def random_password():
    """Generate a random password."""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))

def main(num, file_path, port):
    info = {}
    for i in range(num):
        info["s" + str(i)] = {
            "password": random_password(),
        }
    with open(file_path, "w") as f:
        f.write(json.dumps(info, indent=4))
    
    platform_config = {
        str(port): info
    }
    base_path = os.path.dirname(os.path.abspath(file_path))
    platform_config_path = os.path.join(base_path, "accounts.json")
    with open(platform_config_path, "w") as f:
        f.write(json.dumps(platform_config, indent=4))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate random passwords for students.')
    parser.add_argument('--num', type=int, default=30, help='Number of students to generate')
    parser.add_argument('--file', type=str, default='config/create_students.json', help='File path to save the config')
    parser.add_argument('--port', type=int, default=8001, help='Port to access')
    args = parser.parse_args()

    main(args.num, args.file, args.port)
