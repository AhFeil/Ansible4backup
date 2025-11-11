import os
import subprocess
from typing import Annotated

from fastapi import FastAPI, HTTPException, Header, status
from pydantic import BaseModel


app = FastAPI()

# 通过环境变量传入 API Token 和 ansible 所在虚拟环境
API_TOKEN = os.environ.get('ANSIBLE_API_TOKEN', 'pbDNh6HnihG9Hi9N2Y')
ansible_venv_path = os.environ.get('ANSIBLE_VENV_PATH', '.env')


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
        if result.stderr:
            print("STDERR:", result.stderr)
        # 检查命令是否成功执行
        if result.returncode == 0:
            return {"status": "success", "message": f"{tags} has been processed successfully."}
        else:
            return {"status": "false", "message": f"{tags} failed to be processed"}
    except subprocess.CalledProcessError as e:
        # 如果命令执行失败，subprocess.run 将抛出 CalledProcessError
        print("An error occurred while running ansible-playbook.")
        print(e.output)
        return {"status": "false", "message": e.output}


class AnsibleRequest(BaseModel):
    inventory: str
    playbook: str
    tags: str


# 由于里面是阻塞的，所以不使用异步，而是用线程池进行
@app.post("/ansible_bak_api")
def api_endpoint(request_body: AnsibleRequest, authorization: Annotated[str, Header()]):
    if authorization != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token"
        )

    result = run_ansible_playbook(request_body.inventory, request_body.playbook, request_body.tags, ansible_venv_path)

    return result


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5123)
