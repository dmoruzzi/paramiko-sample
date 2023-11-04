import paramiko
import yaml

def connect(host, username, key_file=None, password=None, port=22):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        if key_file:
            key = paramiko.RSAKey(filename=key_file)
            ssh.connect(host, port, username, pkey=key)
        else:
            ssh.connect(host, port, username)
        return ssh
    except Exception as e:
        print(f"Connection error to {host}: {e}")
        return None

def execute_with_input(ssh, cmd, input_responses=None):
    if ssh:
        stdin, stdout, stderr = ssh.exec_command(cmd)
        if input_responses:
            for response in input_responses:
                stdin.write(response + "\n")
                stdin.flush()
        return stdout.read().decode()
    else:
        return None

def disconnect(ssh):
    if ssh:
        ssh.close()

if __name__ == '__main__':
    with open('config.yaml', 'r') as config_file:
        config = yaml.safe_load(config_file)

    server_configurations = config.get('servers', [])

    # Specify the labels you want to target
    labels_to_use = ["QA", "Development"]

    command_definitions = {
        'uptime': {
            'input_responses': None,
        },
        'yum check-update': {
            'input_responses': None,
        },
        'yum -y update': {
            'input_responses': ['y'],
        }
    }

    for server_info in server_configurations:
        # Check if the server's labels match the labels to use
        if all(label in server_info.get('labels', []) for label in labels_to_use):
            ssh_client = connect(
                server_info['host'],
                server_info['username'],
                server_info['key_file'],
                server_info.get('password'),  # Use the password if provided, or None
                server_info.get('port', 22)  # Use the specified port or default to 22
            )

            if ssh_client:
                for command, definition in command_definitions.items():
                    input_responses = definition['input_responses']
                    output = execute_with_input(ssh_client, command, input_responses)
                    print(f"{server_info['host']}: {command} -> {output}")
                disconnect(ssh_client)
