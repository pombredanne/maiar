import io
import re
import os
import pytest
import sys
from tempfile import TemporaryDirectory
from contextlib import redirect_stdout

from maiar_lib import maiar_lib


def test_any_functions():
    assert maiar_lib.any_in(['a', 'd'], ['a', 'b', 'c']) is True
    assert maiar_lib.any_in(('f', 'd'), ('a', 'b', 'c')) is False

    assert maiar_lib.any_startswith('abc', ('ab', 'cd')) is True
    assert maiar_lib.any_startswith('def', ['ab', 'cd']) is False

    assert maiar_lib.any_startswith_any(('123', 'abc'), ('ab', 'cd')) is True
    assert maiar_lib.any_startswith_any(('bcd', 'def'), ('ab', 'cd')) is False
    assert maiar_lib.any_startswith_any('abc', ('ab', 'cd')) is True


def test_indexes_of():
    assert maiar_lib.indexes_of('a1b2c3', 'a') == [0]
    assert maiar_lib.indexes_of('a1b1c1', '1') == [1, 3, 5]
    assert maiar_lib.indexes_of('aaabc', 'aa') == [0, 1]
    assert maiar_lib.indexes_of('aaabcaa', 'aa', start=1) == [1, 5]


def test_upsert_dicts():
    orig_dict = {'a': 1}
    assert maiar_lib.upsert_dicts(orig_dict, {'b': 2}) == orig_dict

    assert orig_dict['a'] == 1
    assert orig_dict['b'] == 2

    assert maiar_lib.upsert_dicts(orig_dict, {'b': 3}) is False


def test_prints():
    functions = (maiar_lib.print_ok, maiar_lib.print_warn, maiar_lib.print_error)

    msg = 'Test Message'

    for f in functions:
        print_buffer = io.StringIO()
        with redirect_stdout(print_buffer):
            f(msg)

        assert msg in print_buffer.getvalue()


def test_formatted_json():
    assert maiar_lib.formatted_json({'test': 'value'}) == '{\n    "test": "value"\n}'


def test_run_command_output():
    cmd_args = ['ls', '-la']

    success, output = maiar_lib.run_command_output(cmd_args)

    assert success
    assert 'maiar' in output
    assert '..' in output

    success, output = maiar_lib.run_command_output(['false'])

    assert success is False
    assert not output

    cmd_args = ['env']

    success, output = maiar_lib.run_command_output(cmd_args, env={'TEST_ENV': 'value'})

    assert success
    assert 'TEST_ENV=value' in output

    assert maiar_lib.run_shell_command('true', env={'TEST_ENV': 'value'}) == 0

    with pytest.raises(SystemExit):
        maiar_lib.run_shell_command('false', autofail=True)


def test_python_build_environment():
    build_env = maiar_lib.get_python_build_environment()

    assert isinstance(build_env, dict)
    assert 'pytest' in build_env
    assert re.match(r'[0-9]+\.[0-9]+\.[0-9]+', build_env['pytest'])


def test_sha1_hash():
    assert maiar_lib.sha1_hash_from_data({'Test': 'value'}) == 'af288b8982cd79d2a1f26623d9c9b7bcbfeff277'


class MockBlob():
    n_tries = 0

    def __init__(self, n_tries):
        self.n_tries = n_tries

    def download_to_filename(self, local_path):
        if self.n_tries > 0:
            self.n_tries -= 1
            raise RuntimeError('Mock Exception')

        return local_path

    def upload_from_filename(self, local_path):
        if self.n_tries > 0:
            self.n_tries -= 1
            raise RuntimeError('Mock Exception')

        return local_path


def test_download_file_with_retries():
    blob = MockBlob(1)
    assert maiar_lib.download_file_with_retries(blob, 'filename') == 'filename'

    assert blob.n_tries == 0


def test_upload_file_with_retries():
    blob = MockBlob(1)
    assert maiar_lib.upload_file_with_retries(blob, 'filename') == 'filename'

    assert blob.n_tries == 0


def test_detect_repository():
    with TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)

        with pytest.raises(SystemExit):
            maiar_lib.detect_repository('')

        with pytest.raises(SystemExit):
            maiar_lib.detect_repository('sftp://not-a-bucket/')

        assert maiar_lib.detect_repository('gs://example-bucket/') == 'example-bucket'
        assert maiar_lib.detect_repository('gs://example-bucket') == 'example-bucket'

        with open('repository.maiar', 'w') as f:
            f.write('gs://example-bucket-2/')

        assert maiar_lib.detect_repository('') == 'example-bucket-2'

        with open('repository.maiar', 'w') as f:
            f.write('sftp://still-not-a-bucket')

        with pytest.raises(SystemExit):
            maiar_lib.detect_repository('')


def test_linux_os_version():
    if sys.platform.startswith('linux'):
        assert '.' in maiar_lib.get_linux_os_version()
