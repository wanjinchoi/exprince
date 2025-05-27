#!/usr/bin/env python
# coding=utf8
"""
====================================
 :mod:`argoslabs.etc.run_python_script`
====================================
.. moduleauthor:: Duk Kyu Lim <deokyu@argos-labs.com>
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS plugin module
"""
# Authors
# ===========
#
# * Duk Kyu Lim
#
# Change Log
# --------


################################################################################
import sys
import types
import traceback
import subprocess
from alabs.common.util.vvargs import ModuleContext, func_log, \
    ArgsError, ArgsExit, get_icon_path
import re

CONTEXT = '''{code}

import sys
import traceback
import subprocess    

def _run_plugin(cmd):
    with subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
        out = proc.stdout.read().decode('utf-8')
        err = proc.stderr.read().decode('utf-8')
    return out, err

def run_plugin(cmd):
    out, err = _run_plugin(cmd)
    if err:
        raise Exception(f'Plugin {{err}} >> Command: {{cmd}}')
    return out
    
if __name__ == '__main__':
    print(main({arguments}))
'''


###############################################################################
def install(packages):
    packages = packages.replace('\\n', '\n')
    packages = packages.split('\n')
    packages = ' '.join(packages)
    if sys.platform == 'win32':
        import pathlib
        executable = str(pathlib.PureWindowsPath(sys.executable))
    else:
        executable = sys.executable
    executable = '"' + executable + '"'
    cmd = f'{executable} -m pip install {packages} ' \
          f'-i https://pypi-official.argos-labs.com/simple ' \
          f'--trusted-host pypi-official.argos-labs.com -U --no-cache-dir ' \
          f'--disable-pip-version-check'
    proc = subprocess.run(cmd, shell=True, capture_output=True)
    # if error or warning message
    if proc.stderr:
        raise ValueError(proc.stderr.decode('utf-8'))


###############################################################################
def insert_number_each_line(data: str):
    result = list()
    data = data.split('\n')
    for (number, line) in enumerate(data):
        result.append(f'{number + 1:04} {line}')
    return '\n'.join(result)


###############################################################################
def get_kwargs(values):
    # values = ('abc=123', 'def=abc', 'ghi==abc')
    # error = ('123', '=123', ) <-- no key, no value
    # return {'abc': '123', 'def': 'abc', 'ghi': '=abc'}
    result = {}
    for x in values:
        i = x.find('=')
        if -1 == i or 0 == i:
            raise ValueError(
                f'{x} is not key-word type. It must be like abc=123')
        result[x[:i].strip()] = x[i + 1:]
    return result


###############################################################################
@func_log
def run_script(mcxt, argspec):
    mcxt.logger.info('>>>starting...')
    code = ''
    try:
        if not argspec.arguments:
            argspec.arguments = []
        arguments = list(map(lambda x: f'"{x}"', argspec.arguments))
        # preventing to recognize backslash as ESCAPE character
        arguments = [x.replace('\\', '\\\\') for x in arguments]

        if not argspec.key_arguments:
            argspec.key_arguments = []

        # checking key-word arguments
        kwargs = get_kwargs(argspec.key_arguments)

        # wrapping value with quotes
        key_arguments = list()
        for v in argspec.key_arguments:
            key, value = v.split('=')
            value = value.replace("\\", "\\\\")
            key_arguments.append(f'{key}="{value}"')

        arguments = arguments + key_arguments
        arguments = ', '.join(arguments)

        # making the code
        global CONTEXT
        if argspec.python_script:
            code = argspec.python_script
            code = code.replace('\\n', '\n')
            code = code.replace('\\t', '    ')
        else:
            with open(argspec.python_file, 'r', encoding='utf-8') as f:
                code = f.read()

        # check existing the main function
        r = re.compile('def main')
        # if not r.findall(argspec.python_script):
        if not r.findall(code):
            raise ValueError(
                'There is no \'main\' function in your code. '
                'The function is the starting point for this plugin. '
                'It must be in your code.')

        code = CONTEXT.format(code=code, arguments=arguments)

        # install python modules
        if hasattr(argspec, 'requirements') and argspec.requirements:
            install(argspec.requirements)

        # For developing mode. printing assembled code.
        if argspec.code:
            print(code)
            exit(0)

        # making a module with python code
        module = types.ModuleType('user_script')
        exec(code, module.__dict__)

        # run the module
        data = module.main(*argspec.arguments, **kwargs)
        print(data, end='')
        mcxt.logger.info('>>>end...')
        return 0

    except Exception as err:
        traceback.print_exc()

        if argspec.detail_error:
            # inserting number at the each line of code for debugging
            code = insert_number_each_line(code)
            sys.stderr.write('\n' + code + '\n')

        msg = str(err)
        mcxt.logger.error(msg)
        return 1

    finally:
        sys.stdout.flush()
        mcxt.logger.info('>>>end...')


###############################################################################
def _main(*args):
    """
    Build user argument and options and call plugin job function
    :param args: user arguments
    :return: return value from plugin job function
    """
    with ModuleContext(
            owner='Duk Kyu Lim',
            group='DEMO',
            version='1.0.1',
            platform=['windows', 'darwin', 'linux'],
            output_type='text',
            display_name='Python Run Script',
            icon_path=get_icon_path(__file__),
            description='Python Script Runner',
    ) as mcxt:
        mcxt.add_argument('--python_script',
                          input_method='multiline;python',
                          display_name='Python Script',
                          show_default=True,
                          input_group='radio=Code;defalut',
                          help='def main():')
        mcxt.add_argument('--python_file',
                          display_name='Python File',
                          show_default=True,
                          input_method='fileread',
                          input_group='radio=Code',
                          help='my_script.py')

        mcxt.add_argument('-a', '--arguments',
                          display_name='Arguments',
                          show_default=True,
                          input_group='Arguments',
                          action='append',
                          help='abc or 123 - every values treats as string')
        mcxt.add_argument('-k', '--key-arguments',
                          display_name='Keyword Arguments',
                          show_default=True,
                          input_group='Arguments',
                          action='append',
                          help='abc=123 or def="hello world" - '
                               'every values treats as string')

        mcxt.add_argument('-r', '--requirements',
                          display_name='Requirements',
                          input_method='multiline;plain',
                          help='write module list you need to install '
                               'like requirements.txt')

        mcxt.add_argument('-e', '--detail-error', action='store_true',
                          display_name="Detail Error Message",
                          help='print detail error messages')

        # todo: using hidden option: --code option
        mcxt.add_argument('-c', '--code', action='store_true')

        argspec = mcxt.parse_args(args)
        return run_script(mcxt, argspec)


###############################################################################
def main(*args):
    try:
        return _main(*args)
    except ArgsError as err:
        sys.stderr.write('Error: %s\nPlease -h to print help\n' % str(err))
    except ArgsExit as _:
        pass
