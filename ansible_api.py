import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

# 通过环境变量传入 API Token 和 ansible 所在虚拟环境
API_TOKEN = os.environ.get('ANSIBLE_API_TOKEN', 'dwSR3bXYXcLGNiGV')
ansible_venv_path = os.environ.get('ANSIBLE_VENV_PATH', './.env')


def run_ansible_playbook(inventory, playbook, tags, ansible_venv_path):
    # 指定虚拟环境中 ansible-playbook 的完整路径
    ansible_playbook_executable = f"{ansible_venv_path}/bin/ansible-playbook"

    command = [
        ansible_playbook_executable,
        '-i', inventory,
        playbook,
        '--tags={}'.format(tags)
    ]

    try:
        # 使用 subprocess.run 执行命令
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # 打印输出结果
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        # 检查命令是否成功执行
        if result.returncode == 0:
            print("Ansible playbook executed successfully.")
            return {"status": "success", "message": f"{tags} has been processed successfully."}
        else:
            print("Ansible playbook execution failed.")
            return {"status": "false", "message": f"{tags} failed to be processed"}
    except subprocess.CalledProcessError as e:
        # 如果命令执行失败，subprocess.run 将抛出 CalledProcessError
        print("An error occurred while running ansible-playbook.")
        print(e.output)
        return {"status": "false", "message": e.output}


@app.route('/ansible_bak_api', methods=['POST'])
def api_endpoint():
    # 检查 Authorization 头部是否存在且正确
    auth_header = request.headers.get('Authorization')
    if auth_header != API_TOKEN:
        return jsonify({"status": "error", "message": "Invalid or missing API token"}), 401
    # 确保请求的内容类型是 JSON
    if not request.is_json:
        return jsonify({"status": "error", "message": "Missing JSON in request"}), 400
    # 解析 JSON 数据
    content = request.get_json()
    # 验证 JSON 数据包含所需的键
    try:
        inventory = content['inventory']
        playbook = content['playbook']
        tags = content['tags']
    except KeyError as e:
        return jsonify({"status": "error", "message": f"Missing key: {e.args[0]}"}), 400
    # 调用其他函数
    result = run_ansible_playbook(inventory, playbook, tags, ansible_venv_path)
    # 返回结果
    return jsonify(result)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5123)
