# Ansible4backup

使用 Ansible 对服务器的目录进行备份，对 docker、systemd 管理的程序支持关闭重启，支持 API 调用。



目前只支持备份到 minio，因此，需要安装自己的 minio 服务端，并且需要手动到 minio 创建 bucket：backup，

目前每次运行都会删除上一次的备份文件







## 结构

工作目录下：
- backup-example.yaml，样例 playbook
- inventory-example.yaml，样例 主机信息
- role/
	- imagebed_backup
	- mastodon_backup
	- matrix_backup
	- my_minio_client_role



通用备份功能
- 检查剩余空间大小
- 压缩前，关闭程序，压缩后，恢复程序。目前支持 systemd 管理的
- 压缩时可以排除子目录
- 上传导出文件到 minio，删除压缩包


## 使用

### 安装


```sh
mkdir -p ~/pythonServe/ && cd ~/pythonServe/
```

```sh
git clone https://git.ahfei.blog/ahfei/Ansible4backup && cd Ansible4backup
```

```sh
sudo apt update && sudo apt upgrade && sudo apt install python3 python3-venv -y
```

```sh
python3 -m venv .env
```

```bash
source .env/bin/activate && pip install -r requirements.txt
```



### inventory.yaml

首先复制 inventory-example.yaml 文件，比如新文件名称为 `inventory.yaml`

```sh
vim inventory.yaml
```

放入被控端的信息

```yaml
backup_hosts:
  vars:
    backup_date: "{{ lookup('pipe', 'date +%Y%m%d') }}"
    minio_alias: ansible4bak
    bucket_name: backup
  hosts:
    MatrixServer:
      ansible_host: <MatrixServer_IP>    # 替换为 MatrixServer 的 IP 地址
      ansible_port: <MatrixServer_Port>  # 替换为 MatrixServer 的 SSH 端口
      ansible_user: <your_username>      # 替换为登录 MatrixServer 的用户名
      ansible_ssh_pass: <your_password>  # 替换为登录密码
      ansible_become_method: sudo
      ansible_become_password: <your_password>  # 替换为登录密码，用于使用 sudo 权限
```

然后配置密钥登录


*测试能否连接上被控端*

测试属于 backup_hosts 的机器

```sh
ansible -i inventory.yaml -m ping backup_hosts
```

单独测试一个机器

```sh
ansible -i inventory.yaml -m ping TechniqueServer
```

---


如果希望用密码登录被控端，需要增加 ansible_ssh_pass 变量

```yaml
backup_hosts:
  vars:
    backup_date: "{{ lookup('pipe', 'date +%Y%m%d') }}"
    minio_alias: ansible4bak
    bucket_name: backup
  hosts:
    MatrixServer:
      ansible_host: <MatrixServer_IP>
      ansible_port: <MatrixServer_Port>
      ansible_user: <your_username>
      ansible_ssh_pass: <your_password>
      ansible_become_method: sudo
      ansible_become_password: <your_password>
```

为了能通过密码登陆，还需要安装 sshpass：

```sh
sudo apt install sshpass
```

并且要先手动登陆一次

```sh
ssh -p 22 username@1.2.3.4
```

这样之后，调用 ansible 执行 playbook 时，就能顺利登录被控端了





## playbook




### 创建剧本










### 执行剧本











## role

创建一个 role，需要在项目目录下的 roles 目录下新建 role 的目录。

```sh
mkdir -p roles/check_storage_space
```

然后，role 的 task 部分，应该放在 tasks 文件中

```sh
mkdir roles/check_storage_space/tasks
```

一般，只用创建一个 main.yaml，代码都放在里面就行

```sh
vim roles/check_storage_space/tasks/main.yaml
```

如果需要 handler 部分，那应该在 handlers 文件中，新建 main.yaml；其他类同。




### role 检查存储空间


确保在运行 playbook 时定义了下面两个变量
1. `large_directory`： 要备份的目录
2. `temporary_store_directory`： 备份文件临时存放的目录，如果不存在，则不比较

如果 `large_directory` 的大小超过了 `temporary_store_directory` 所在硬盘的剩余空间，这个备份任务终止。




### Matrix


*在 playbook 中调用 role*

```sh
vim backup.yaml
```

```yml
- name: Backup Matrix
  tags: 
    - backup_matrix
  hosts: MatrixServer
  vars:
    large_directory: /matrix/synapse/storage/media-store   # 如果存在，则比较硬盘剩余空间与该目录大小
    temporary_store_directory: /tmp/matrix_bak/   # 必须带 /
    specify_directory_in_bucket: MatrixServer
  roles:
    - check_storage_space
    - my_minio_client_role
    - matrix_backup
  tasks:
    - name: delete mc config
      shell: "mc alias rm {{ minio_alias }}"
```

检查 playbook 本身有无问题

```bash
ansible-playbook -i inventory.yaml backup.yaml --tags=backup_matrix --check
```

运行 playbook ：

```bash
ansible-playbook -i inventory.yaml backup.yaml --tags=backup_matrix
```



### Systemd 通用


适用对象，程序是由 systemd 管理的，并且要备份的全在一个目录内。

可以实现，备份前关闭程序，备份后重启；忽略一些子目录。


*在 playbook 中调用 role*

```sh
vim backup.yaml
```

以 minio 图床为例

```yml
- name: Backup Imagebed
  tags: 
    - backup_imagebed
  hosts: ImagebedServer
  vars:
    temporary_store_directory: /tmp/imagebed_bak   # 不能带 /
    imagebed_directory: /mnt/minio
    excluded_directory: --exclude=/mnt/minio/updatefetch --exclude=/mnt/minio/upload # 目前只会这样，以后完善
    specify_directory_in_bucket: ImagebedServer
    systemdservice_name_list: [minio]
    large_directory: "{{ imagebed_directory }}"
  roles:
    - check_storage_space
    - my_minio_client_role
    - imagebed_backup
  tasks:
    - name: delete mc config
      shell: "mc alias rm {{ minio_alias }}"
```

检查 playbook 本身有无问题

```bash
ansible-playbook -i inventory.yaml backup.yaml --tags=backup_imagebed --check
```

运行 playbook ：

```bash
ansible-playbook -i inventory.yaml backup.yaml --tags=backup_imagebed
```


### Docker 通用

类似 systemd，自动关闭重启，docker 一般只有一个目录，只支持备份一个目录。



*在 playbook 中调用 role*

```sh
vim backup.yaml
```

Docker 版的 WordPress

```yml
- name: Backup FlightBorne
  tags: 
    - backup_flight_borne
  hosts: FlightBorneServer
  vars:
    backup_file_name_prefix: wordpress_flight_borne_bak
    temporary_store_directory: /tmp/flight_borne_bak   # 不能带 /
    specify_directory_in_bucket: FlightBorneServer
    container_name_list: [wordpress, wp_mysql, wp_redis]
    container_directory: "{{ ansible_env.HOME }}/myserve/wordpress"
    large_directory: "{{ container_directory }}"
  roles:
    - check_storage_space
    - my_minio_client_role
    - docker_backup
  tasks:
    - name: delete mc config
      shell: "mc alias rm {{ minio_alias }}"
```

```bash
ansible-playbook -i inventory.yaml backup.yaml --tags=backup_flight_borne --check
```



### WordPress

原生安装的，使用 MySQL 系的数据库。

备份前会开启维护模式。

WordPress 备份的内容只有两个，一个网页目录，还有数据库的备份。因此需要提供目录路径和数据库的用户、密码、数据库名称。


*在 playbook 中调用 role*

```sh
vim backup.yaml
```

```yml
- name: Backup Technique
  tags: 
    - backup_technique
  hosts: TechniqueServer
  vars:
    temporary_store_directory: /tmp/technique_bak   # 不能带 /
    specify_directory_in_bucket: TechniqueServer
    systemdservice_name_list: [lsws]
    mysql_user: wp_user
    mysql_password: password
    mysql_dbname: wp_db
    wordpress_directory: /usr/local/lsws/wordpress
    large_directory: "{{ wordpress_directory }}"
  roles:
    - check_storage_space
    - my_minio_client_role
    - wordpress_backup
  tasks:
    - name: delete mc config
      shell: "mc alias rm {{ minio_alias }}"
```

```bash
ansible-playbook -i inventory.yaml backup.yaml --tags=backup_technique --check
```



### NextCloud

原生安装的，使用 MySQL 系的数据库。

备份前会开启维护模式。

同为 PHP 项目，NextCloud 备份的内容也是只有两个，一个网页目录，还有数据库的备份。因此需要提供目录路径和数据库的用户、密码、数据库名称。



*在 playbook 中调用 role*

```sh
vim backup.yaml
```

```yml
- name: Backup NextCloud
  tags: 
    - backup_nextcloud
  hosts: NextCloudServer
  vars:
    temporary_store_directory: /tmp/nextcloud_bak   # 不能带 /
    specify_directory_in_bucket: NextCloudServer
    nextcloud_directory: /var/www/nextcloud.ahfei.blog
    mysql_user: nextcloud
    mysql_password: password
    mysql_dbname: nextcloud_db
    large_directory: "{{ nextcloud_directory }}"
  roles:
    - check_storage_space
    - my_minio_client_role
    - nextcloud_backup
  tasks:
    - name: delete mc config
      shell: "mc alias rm {{ minio_alias }}"
```

```bash
ansible-playbook -i inventory.yaml backup.yaml --tags=backup_nextcloud --check
```





## 调用 API 执行备份


```sh
sudo ufw allow 5123 comment ansible_api
```

运行


```sh
export ANSIBLE_API_TOKEN="dwSR3bXYXcLGNiGV"
export ANSIBLE_VENV_PATH="./.env"
```

```sh
python ansible_api.py
```


### 测试




程序内的测试

```sh
# 虚拟环境的路径
ansible_virtual_env_path = '/home/vfly2/pythonServe/Ansible4backup/.env'
inventory = "/home/vfly2/pythonServe/Ansible4backup/inventory.yaml"
playbook = "/home/vfly2/pythonServe/Ansible4backup/backup.yaml"
tags = 'backup_matrix'

# 调用函数执行 ansible-playbook 命令
run_ansible_playbook(inventory, playbook, tags, ansible_virtual_env_path)
```

调用 API 测试

```sh
curl -X POST -H "Content-Type: application/json" -H "Authorization: pbDNh6HnihG9Hi9N2Y" -d '{"inventory":"/home/vfly2/pythonServe/Ansible4backup/inventory.yaml", "playbook":"/home/vfly2/pythonServe/Ansible4backup/backup.yaml", "tags":"backup_matrix"}' http://ip:5123/ansible_bak_api
```




### 持久化运行



```sh
sudo vim /lib/systemd/system/ansible_api.service
```

```ini
[Unit]
Description=ansible API Server
After=network.target

[Service]
WorkingDirectory=/home/vfly2/pythonServe/Ansible4backup
User=vfly2
Group=vfly2
Type=simple
ExecStart=/home/vfly2/pythonServe/Ansible4backup/.env/bin/python /home/vfly2/pythonServe/Ansible4backup/ansible_api.py
ExecStop=/bin/kill -s HUP $MAINPID
Environment=PYTHONUNBUFFERED=1
RestartSec=15
Restart=on-failure

[Install]
WantedBy=default.target
```

```sh
sudo systemctl daemon-reload
```

```sh
sudo systemctl enable --now ansible_api
```

```sh
sudo systemctl status ansible_api
```

```sh
sudo systemctl stop ansible_api
```

```sh
sudo systemctl start ansible_api
```














