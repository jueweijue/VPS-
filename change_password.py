import paramiko
import time

print("本脚本用于远程修改主机密码")
# 设置旧主机信息
hostname = input("请输入主机IP：")
port = input("请输入端口号(默认22)：") or 22
username = input("请输入主机用户名：")
password = input("请输入主机密码：")
new_password = input("请输入新密码：")


# 建立SSH连接
def connect_host(hostname, port, username, password):
    try:
        # 创建SSH对象
        ssh = paramiko.SSHClient()
        # 允许连接不在know_hosts文件中的主机
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # 连接服务器
        ssh.connect(hostname=hostname, port=port, username=username, password=password)
        print("连接成功")
        return ssh
    except Exception as e:
        return False


# 修改密码
def change_passwd(ssh, new_password):
    try:
        print("正在修改密码...")
        shell = ssh.invoke_shell()
        time.sleep(3)
        shell.sendall("passwd\r\n")
        time.sleep(1)
        shell.sendall(new_password + "\r\n")
        time.sleep(1)
        shell.sendall(new_password + "\r\n")
        time.sleep(1)
    except Exception as e:
        print("修改失败，错误类型：" + str(e))
    finally:
        ssh.close()


# 验证是否成功
def check_old_passwd():
    print("正在使用旧密码连接主机...")
    check = connect_host(hostname, port, username, password)
    if check:
        print("修改密码失败，旧密码仍可用")
        check.close()
    else:
        print("修改密码成功，旧密码已失效")


# 主函数
def main():
    ssh = connect_host(hostname, port, username, password)
    if not ssh:
        print("连接失败")
        exit(1)
    change_passwd(ssh, new_password)
    ssh.close()
    check_old_passwd()


if __name__ == "__main__":
    main()
