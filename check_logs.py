import re

def check_logs(log_file):
    with open(log_file, 'r') as file:
        logs = file.readlines()

    for line in logs:
        if re.search(r'ERROR|WARNING', line):
            print(line.strip())

if __name__ == "__main__":
    check_logs('pi_share_receiver.log')
