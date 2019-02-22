import sys
import subprocess
import time
import json
import os
from hashlib import sha1


COLOR_TO_CODE = {
    'black': 30,
    'red': 31,
    'green': 32,
    'yellow': 33,
    'blue': 34,
    'magenta': 35,
    'cyan': 36,
    'white': 37,
    'reset': 0,
}


def color_start(color):
    print('\u001b[' + str(COLOR_TO_CODE[color]) + 'm', end='')


def color_end():
    print('\u001b[0m', end='')


def print_color(str, color):
    color_start(color)
    print(str)
    color_end()


def print_ok(msg):
    print_color(msg, 'green')


def print_warn(msg):
    print_color(f'WARN: {msg}', 'yellow')


def print_error(msg):
    print_color(f'ERROR: {msg}', 'red')


def print_fatal(msg):
    print_color(f'FATAL ERROR: {msg}', 'red')
    sys.exit(1)


def any_in(test, search_within):
    for t in test:
        if t in search_within:
            return True

    return False


def any_startswith(element, test_startswith):
    for t in test_startswith:
        if element.startswith(t):
            return True

    return False


def any_startswith_any(elements, test_startswith):
    if not isinstance(elements, (list, tuple)):
        elements = [elements]

    for e in elements:
        for t in test_startswith:
            if e.startswith(t):
                return True

    return False


def indexes_of(subject, search, start=0):
    indexes = []

    while True:
        next_index = subject.find(search, start)
        if next_index < 0:
            break

        indexes.append(next_index)
        start = next_index + 1

    return indexes


def upsert_dicts(orig_dict, new_dict):
    for key, value in new_dict.items():
        if key in orig_dict:
            print_error(f'{key} specified twice!')
            return False

        orig_dict[key] = value

    return orig_dict


def formatted_json(value):
    return json.dumps(value, indent=4, sort_keys=True)


def run_command_output(cmd_args, env=None, fail_ok=False):
    if env:
        env = {**os.environ, 'PWD': os.getcwd(), **env}

    result = subprocess.run(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    if result.returncode != 0 and not fail_ok:
        print_error(f'Process failed: {" ".join(cmd_args)}')
    return (result.returncode == 0, str(result.stdout, 'utf-8'))


def run_shell_command(cmd_str, env=None, autofail=False):
    if env:
        env = {**os.environ, 'PWD': os.getcwd(), **env}

    result = subprocess.run([cmd_str], env=env, shell=True)
    if autofail and result.returncode != 0:
        print_fatal(f'Process failed: {cmd_str}')
    return result.returncode


def get_linux_os_version():
    success, output = run_command_output(['lsb_release', '-a'])
    if not success:
        return None

    distribution = None
    version = None

    for line in output.split('\n'):
        if line.startswith('Distributor ID:'):
            distribution = line[line.find(':') + 1:].lower().strip()
        elif line.startswith('Release:'):
            version = line[line.find(':') + 1:].lower().strip()

    if not version or not distribution:
        return None

    return f'{distribution}.{version}'


def get_system_build_environment():
    success, output = run_command_output(['dpkg', '-l'])
    if not success or not output:
        print(output)
        print_fatal('Could not get list of installed packages from dpkg!')

    build_env = {}

    separator_points = None

    for line in output.split('\n'):
        if line.startswith('+') and not separator_points:
            separator_points = indexes_of(line, '-')
            if len(separator_points) < 4:
                print_fatal(f'Could not parse separator line while parsing dpkg output: {line}')

        if not line or not line.startswith('i'):
            continue

        if not separator_points:
            print_fatal(f'Did not find separator line while parsing dpkg output!')

        # Some of these fields are not needed, but are left in incase we want to track that in the future.
        # status = line[:separator_points[0]].strip()
        name = line[separator_points[0] + 1:separator_points[1]].strip()
        version = line[separator_points[1] + 1:separator_points[2]].strip()
        # architecture = line[separator_points[2] + 1:separator_points[3]].strip()
        # description = line[separator_points[3] + 1:].strip()

        build_env[name] = version

    return build_env


def get_python_build_environment():
    success, output = run_command_output(['pip3', 'list'])
    if not success or not output:
        print(output)
        print_fatal('Could not get list of installed packages from pip3!')

    build_env = {}

    separator_points = None

    for line in output.split('\n'):
        if line.startswith('-') and not separator_points:
            separator_points = indexes_of(line, ' ')
            if len(separator_points) < 1:
                print_fatal(f'Could not parse separator line while parsing pip3 output: {line}')

        if not line or line.startswith('Package '):
            continue

        name = line[:separator_points[0]].strip()
        version = line[separator_points[0] + 1:].strip()

        build_env[name] = version

    return build_env


def detect_repository(repo_path):
    if not repo_path:
        if os.path.exists('repository.maiar'):
            with open('repository.maiar') as f:
                repo_path = f.read().strip()
            if not repo_path or not repo_path.startswith('gs://'):
                print_fatal('No valid repository found in repository.maiar, '
                            'please write the repository as the only element in the file, '
                            'or provide the repository with --repository on the command line')
        else:
            print_fatal('No repository.maiar file found, either write the repository as the only '
                        'element in that file, or provide the repository with --repository '
                        'on the command line')

    if not repo_path.startswith('gs://'):
        print_fatal('Repository must be a google cloud storage bucket')

    repo_path = repo_path[5:].strip().strip('/')

    return repo_path


def sha1_hash_from_data(data):
    return sha1(json.dumps(data).encode('utf-8')).hexdigest()


def download_file_with_retries(blob, local_path):
    err = None
    for retry in range(8):
        try:
            return blob.download_to_filename(local_path)
        except Exception as e:
            print(f'Caught exception and retrying: {e}')
            err = e
            time.sleep(1 + 2 * retry)

    raise err


def upload_file_with_retries(blob, local_path):
    err = None
    for retry in range(8):
        try:
            return blob.upload_from_filename(local_path)
        except Exception as e:
            print(f'Caught exception and retrying: {e}')
            err = e
            time.sleep(1 + 2 * retry)

    raise err
