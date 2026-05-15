import os
import subprocess
from typing import Annotated, Optional

from fastapi import FastAPI, HTTPException, Header, status
from pydantic import BaseModel


app = FastAPI()

# 通过环境变量传入 API Token 和 ansible 所在虚拟环境
API_TOKEN = os.environ.get('ANSIBLE_API_TOKEN', 'pbDNh6HnihG9Hi9N2Y')
ansible_venv_path = os.environ.get('ANSIBLE_VENV_PATH', '.env')


def run_ansible_playbook(inventory, playbook, tags, ansible_venv_path, extra_vars=None):
    # 指定虚拟环境中 ansible-playbook 的完整路径
    ansible_playbook_executable = f"{ansible_venv_path}/bin/ansible-playbook"

    command = [
        ansible_playbook_executable,
        '-i', inventory,
        playbook,
        '--tags={}'.format(tags)
    ]

    if extra_vars:
        command.extend(['-e', extra_vars])

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        return {
            "status": "false",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }

    return {"status": "success", "stdout": result.stdout}

class AnsibleRequest(BaseModel):
    inventory: str
    playbook: str
    tags: str
    extra_vars: Optional[str] = None


# 由于里面是阻塞的，所以不使用异步，而是用线程池进行
@app.post("/ansible_bak_api")
def api_endpoint(request_body: AnsibleRequest, authorization: Annotated[str, Header()]):
    if authorization != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token"
        )

    result = run_ansible_playbook(request_body.inventory, request_body.playbook, request_body.tags, ansible_venv_path, request_body.extra_vars)

    if result["status"] != "success":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result
        )

    return result


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5123)
