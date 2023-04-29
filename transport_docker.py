import paramiko
import os
import time


def backup_container_volume(ssh, docker_path):
    """备份容器数据卷"""
    dir_path, file_name = os.path.split(docker_path)
    try:
        command = f"cd {dir_path} && tar -zcvf {file_name}.tar.gz {file_name}"
        stdin, stdout, stderr = ssh.exec_command(command)
        print("正在备份...")
        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                print(stdout.channel.recv(1024).decode(), end="")
    except Exception as e:
        print(f"备份容器数据卷失败，错误类型：{e}")
        return False
    return True


def transfer_backup_file(
    ssh,
    new_hostname,
    new_port,
    new_username,
    new_password,
    new_docker_path,
    docker_path,
):
    """传输备份文件"""
    dir_path, file_name = os.path.split(docker_path)
    try:
        shell = ssh.invoke_shell()
        time.sleep(3)
        command = f"scp -P {new_port} -r {dir_path}/{file_name}.tar.gz \
            {new_username}@{new_hostname}:{new_docker_path}"
        shell.sendall(command + "\r\n")
        time.sleep(1)
        shell.sendall(new_password + "\r\n")
        print("正在传输...")
        # 命令执行完成的标志
        command_finished = False
        while not command_finished:
            if shell.recv_ready():
                output = shell.recv(1024).decode("utf-8")
                print(output, end="")
                if "100%" in output:
                    command_finished = True
                    shell.close()
    except Exception as e:
        print(f"传输容器数据卷失败，错误类型：{e}")
        return False
    return True


def deploy_new_container(new_ssh, new_docker_path, file_name):
    """部署新容器"""
    try:
        command = f"cd {new_docker_path} && tar -zxvf {file_name}.tar.gz \
            && rm -rf {file_name}.tar.gz && cd {file_name} && docker-compose up -d"
        print("\n正在部署新容器...")
        stdin, stdout, stderr = new_ssh.exec_command(command)
        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                print(stdout.channel.recv(1024).decode(), end="")
    except Exception as e:
        print(f"部署新容器失败，错误类型：{e}")
        return False
    return True


def main():
    print("本脚本用于将旧主机docker容器备份并转移到新主机上，仅适用于docker compose部署的容器")
    # 设置旧主机信息
    hostname = input("请输入备份主机IP：")
    port = 22  # 默认端口号22
    username = input("请输入备份主机用户名：")
    password = input("请输入备份主机密码：")
    docker_path = input("请输入容器数据卷所在路径(默认备份在上一级目录)：")
    # 设置新主机信息
    new_hostname = input("请输入目标主机IP：")
    new_port = 22  # 默认端口号22
    new_username = input("请输入目标主机用户名：")
    new_password = input("请输入目标主机密码：")
    new_docker_path = input("请输入容器数据卷所在路径：")

    # 建立SSH连接
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=hostname, port=port, username=username, password=password)
    # 备份容器数据卷
    if not backup_container_volume(ssh, docker_path):
        ssh.close()
        return
    # 传输备份文件
    if not transfer_backup_file(
        ssh,
        new_hostname,
        new_port,
        new_username,
        new_password,
        new_docker_path,
        docker_path,
    ):
        ssh.close()
        return
    ssh.close()
    # 建立新主机SSH连接
    new_ssh = paramiko.SSHClient()
    new_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    new_ssh.connect(
        hostname=new_hostname,
        port=new_port,
        username=new_username,
        password=new_password,
    )
    # 部署新容器
    dir_path, file_name = os.path.split(docker_path)
    if not deploy_new_container(new_ssh, new_docker_path, file_name):
        new_ssh.close()
        return
    new_ssh.close()
    print("转移容器成功！")


if __name__ == "__main__":
    main()
