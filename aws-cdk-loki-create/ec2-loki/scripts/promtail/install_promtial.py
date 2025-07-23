"""
Script to install promtail and with a configuration file
that forwards to Loki server running in the account.
"""
import enum
import shutil
import subprocess
import urllib.request
import zipfile
import os
import sys
import re
from typing import Optional

PROMTAIL_BIN_DIR = "/usr/local/bin/"
PROMTAIL_CONF_DIR = "/local/promtail/"

candidate_log_paths = [
    '/local/dip/logs/*.log',
    '/var/log/*.log',
    '/srv/{service}/*.log'
]

# Template for promtail config, needs Loki-URL to be set.
promtail_config_template = """
server:
  http_listen_port: 9080
  grpc_listen_port: 0
 
positions:
  filename: /local/promtail/positions.yaml
 
clients:
        - url: http://%%loki_url%%/loki/api/v1/push
 
scrape_configs:
  - job_name: ec2-logs
    static_configs:
    - targets:
        - localhost
      labels:
        job: "{{EC2_INSTANCE_ID}}"
        __path__: /local/dip/logs/*.log
 
    pipeline_stages:
    - match:
        selector: '{job="ec2-logs"}'
        stages:
          - regex:
             expression: |
               "^(?P<timestamp>\\S+ \\S+ \\S+) (?P<log>.*)"
"""

# Content of file to set up under systemctl
promtail_service_file = """
[Unit]
Description=Promtail
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/promtail-linux-amd64 -config.file=/local/promtail/promtail-config.yaml
Restart=always

[Install]
WantedBy=multi-user.target
"""


class InstallOption(enum.Enum):
    """The install option for promtail, or INSTALLED if already there"""
    DOCKER = 'docker'
    LOCAL = 'local'
    INSTALLED = 'installed'


def check_install_options() -> InstallOption:
    """Check the system to identify if already installed and if not which option to use"""

    docker_path = shutil.which("docker")
    if docker_path:
        #return InstallOption.DOCKER
        print("This instance has docker, but will install locally anyway.")

    return InstallOption.LOCAL


def install_local_promtail() -> str:
    """
    Do the following commands:
    > sudo mkdir /opt/promtail & cd /opt/promtail
    > curl -O -L “https://github.com/grafana/loki/releases/download/v1.5.0/promtail-linux-amd64.zip”
    > sudo unzip “promtail-linux-amd64.zip”
    > sudo chmod a+x “promtail-linux-amd64"

    :return: path to where the config file should go
    """
    exec_file = "promtail-linux-amd64"
    zip_file = f"{exec_file}.zip"
    grafana_local_url = f"https://github.com/grafana/loki/releases/download/v1.5.0/{zip_file}"
    promtail_path = "/usr/local/bin"

    print(f"install promtail: {promtail_path=} {exec_file=} {zip_file=} {grafana_local_url=}")

    urllib.request.urlretrieve(grafana_local_url, zip_file)

    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(promtail_path)

    chmod_path = f"{promtail_path}/{exec_file}".format(promtail_path=promtail_path, exec_file=exec_file)
    os.chmod(chmod_path, 0o755)

    return "/local/promtail"


def install_docker_promtail() -> str:
    """
    Do the following commands:
    > wget https://raw.githubusercontent.com/grafana/loki/v2.9.4/clients/cmd/promtail/promtail-docker-config.yaml -O promtail-config.yaml
    > docker run --name promtail -d -v $(pwd):/mnt/config -v /var/log:/var/log --link loki grafana/promtail:2.9.4 -config.file=/mnt/config/promtail-config.yaml

    :return: str - path to where the config file should go.
    """
    promtail_docker_url = "https://raw.githubusercontent.com/grafana/loki/v2.9.4/clients/cmd/promtail/promtail-docker-config.yaml"
    output_file = "/opt/promtail/promtail-config.yaml"

    urllib.request(promtail_docker_url, output_file)

    return "/local/promtail"


def install_promtail(option: InstallOption) -> str:
    """
    Install promtail with either DOCKER or LOCAL option.
    :param option:
    :return: str - path to where config should be installed or NONE if installed already
    """
    if option == InstallOption.LOCAL:
        return install_local_promtail()
    elif option == InstallOption.DOCKER:
        return install_docker_promtail()
    elif option == InstallOption.INSTALLED:
        return None


def get_instance_id_from_metadata() -> Optional[str]:
    """ curl the AWS meta-data IP to get instance info """
    url = "http://169.254.169.254/latest/meta-data/instance-id"
    try:
        with urllib.request.urlopen(url) as response:
            if response.getcode() == 200:
                return response.read().decode("utf-8")
            else:
                print(f"Failed to retrieve instance ID. Status code: {response.getcode()}")
                return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def create_promtail_config(option: InstallOption, config_dir: str, loki_url: str, ec2_inst_id: Optional[str]) -> None:
    """ Create the config, but scanning possible log locations and including them in config """

    # Put in Loki URL into config
    promtail_config_content = promtail_config_template.replace("%%loki_url%%", loki_url)

    # Put EC2 Instance ID into config file if available.
    if ec2_inst_id:
        promtail_config_content = promtail_config_content.replace("{{EC2_INSTANCE_ID}}", ec2_inst_id)

    # Place the file
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    config_file_path = f"{config_dir}/promtail-config.yaml"

    with open(config_file_path, 'w') as config_file:
        config_file.write(promtail_config_content)


def configure_as_systemctl_service(install_option: InstallOption, config_dir: str) -> None:
    """ Configure promtail work under systemctl """

    if install_option == InstallOption.DOCKER:
        print("Promtail running under DOCKER doesn't need systemctl")
        return None

    systemd_file_path = "/etc/systemd/system"
    promtail_service_path = f"{systemd_file_path}/promtail.service"

    with open(promtail_service_path, 'w') as service_file:
        service_file.write(promtail_service_file)

    os.chmod(promtail_service_path, 644)

    daemon_reload_cmd = ["sudo", "systemctl", "daemon-reload"]
    enable_start_on_boot_cmd = ["sudo", "systemctl", "enable", "promtail"]

    try:
        subprocess.run(daemon_reload_cmd, check=True)
        subprocess.run(enable_start_on_boot_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to configure systemctl. Reason: {e}")
        raise ValueError(f"Failed to configure systemctl. Reason: {e}")


def start_promtail(option: InstallOption, config_file_path: str) -> None:
    """ Try to start promtail, either with docker or standard method. """

    local_command = ["sudo", "systemctl", "restart", "promtail"]

    docker_command = [
    "docker", "run", "--name", "promtail", "-d",
    "-v", "$(pwd):/mnt/config", "-v", "/var/log:/var/log",
    "--link", "loki", "grafana/promtail:2.9.4",
    "-config.file=/mnt/config/promtail-config.yaml"
    ]

    try:
        if option == InstallOption.DOCKER:
            subprocess.run(docker_command, check=True)
        if option == InstallOption.LOCAL:
            subprocess.run(local_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"FAILED to start promtail. Reason: {e}")
        raise ValueError(f"FAILED to start promtail. Reason: {e}")


def is_valid_ip_port(ip_port_str):
    """ Regular expression pattern for IP:port format """

    pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}$'

    # Match the pattern
    if re.match(pattern, ip_port_str):
        return True
    else:
        return False


def main(params) -> None:
    """
    Command line should look like:
       > python3 install_promtail.py <loki_url_port>

    Example:
       > python3 install_promtail.py "10.0.0.197:3100"

    :param params: List[str] - only one parameter which is the Loki-IP and port.
    """

    # verify loki_url is in command line
    if not params or len(params) != 1:
        raise ValueError(f'Command line has one required parameter - loki_url.'
                         f' Example: python3 install_promtail.py "10.0.0.42:3100"')

    # verify loki_url is in IP:port format.
    loki_url: str = params[0]
    if not is_valid_ip_port(loki_url):
        raise ValueError(f'Input param not valid ip port format. Should be like "10.0.0.42:3100". Was {loki_url}')

    ec2_inst_id = get_instance_id_from_metadata()

    install_option = check_install_options()
    config_dir = install_promtail(install_option)
    if config_dir:
        create_promtail_config(install_option, config_dir, loki_url, ec2_inst_id)
        configure_as_systemctl_service(install_option, config_dir)
        start_promtail(install_option, config_dir)


if __name__ == "__main__":
    main(sys.argv[1:])
