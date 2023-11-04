import paramiko
import yaml
import logging

# Configure logging
log_format = "%(asctime)s [%(levelname)s]: %(message)s"
logging.basicConfig(filename='ssh_operations.log', level=logging.DEBUG, format=log_format)  # Set the log level to DEBUG

def connect(host, username, key_file=None, password=None, port=22):
    logging.debug(f"Connecting to {host}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        if key_file:
            key = paramiko.RSAKey(filename=key_file)
            ssh.connect(host, port, username, pkey=key)
        else:
            ssh.connect(host, port, username)
        logging.debug(f"Connected to {host}.")
        return ssh
    except Exception as e:
        error_msg = f"Connection error to {host}: {e}"
        logging.error(error_msg)  # Log the error
        return None

def execute_with_input(ssh, cmd, input_responses=None):
    if ssh:
        logging.debug(f"Executing command: {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        if input_responses:
            for response in input_responses:
                stdin.write(response + "\n")
                stdin.flush()
        output = stdout.read().decode()
        logging.debug(f"Command '{cmd}' executed with output: {output}")  # Debug log
        return output
    else:
        return None

def disconnect(ssh):
    if ssh:
        host = ssh.get_transport().getpeername()[0]
        logging.debug(f"Disconnecting from {host}...")
        ssh.close()
        logging.debug(f"Disconnected from {host}.")
        return None  # Reset the ssh_client

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
                    log_message = f"{server_info['host']}: {command} -> {output}"
                    logging.info(log_message)
                ssh_client = disconnect(ssh_client)
