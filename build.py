import os
import sys
import shutil
import pickle

from subprocess import PIPE, Popen
from fnmatch import fnmatch

import configuration as config # Edit 'configuration.py' to edit build settings

# BUILD_DATA is a dictionary containing timestamps
# for file modifications between builds.
BUILD_DATA = dict()


def _change_extension(old_filename, extension):
    filename, _ = os.path.splitext(old_filename)
    return f'{filename}{extension}'


def _file_is_new_or_modified(source):
    global BUILD_DATA

    build_data_modified = BUILD_DATA.get(source, 0)
    system_modified     = os.path.getmtime(source)

    if system_modified > build_data_modified:
        BUILD_DATA[source] = system_modified
        return True

    return False


def _check_and_copy(source, destination):
    global BUILD_DATA

    # If the file exists within destination but not within source,
    # delete it and remove it from the database.
    if (not os.path.exists(source)) and os.path.exists(destination):
        log(0, f'- {os.path.normpath(source)}')
        BUILD_DATA.pop(source)
        os.remove(destination)
        return

    if _file_is_new_or_modified(os.path.normpath(source)):
        log(0, f'+ {os.path.normpath(source)}')
        shutil.copy2(source, destination)


def _check_and_ignore(source, paths):
    ignore_list     = None
    paths_to_ignore = list()

    if config.LOC_SRC in source:
        ignore_list = 'SRC'
    elif config.LOC_LIB in source:
        ignore_list = 'LIB'
    elif config.LOC_RES in source:
        ignore_list = 'RES'

    if ignore_list != None:
        for path in paths:
            for glob in config.IGNORE[ignore_list]:
                if fnmatch(path, glob):
                    paths_to_ignore.append(path)

    return paths_to_ignore


def _flatten_directory(source):
    return [
        os.path.normpath(os.path.join(path[0], file)) # Path[0] is the parent directory.
        for path in os.walk(source)                   # Get every sub-directory/file in 'source.'
        for file in path[2]                           # Get every filename in 'path.'
    ]


def run_external_tool(command) -> (bool, str):
    process = Popen(command, stdout=PIPE, stderr=PIPE)
    _, output = process.communicate()
    exit_code = process.returncode

    if exit_code == 0:
        return (True, '')

    return (False, output.decode('utf-8'))


def apply_source_changes_to_destination(source, destination):
    global BUILD_DATA

    flat_source      = _flatten_directory(source)
    flat_destination = _flatten_directory(destination)

    for destination_file in flat_destination:
        filename = os.path.basename(destination_file)
        matches  = list(filter(lambda path: filename in path, flat_source))

        if len(matches) <= 0:
            log(0, f'- {os.path.join(source, filename)}')
            os.remove(destination_file)


def prepare_build_directory():
    assets_directory = os.path.join(config.LOC_BUILD, config.LOC_RES)
    apply_source_changes_to_destination(config.LOC_RES, assets_directory)

    try:
        shutil.copytree(config.LOC_SRC, config.LOC_BUILD, dirs_exist_ok=True, ignore=_check_and_ignore, copy_function=_check_and_copy)
        shutil.copytree(config.LOC_LIB, config.LOC_BUILD, dirs_exist_ok=True, ignore=_check_and_ignore, copy_function=_check_and_copy)
        shutil.copytree(config.LOC_RES, assets_directory, dirs_exist_ok=True, ignore=_check_and_ignore, copy_function=_check_and_copy)
    except Exception as error:
        log(2, f'Unable to copy file. Reason: {error}')


def default_build():
    log(0, 'Starting standard build.')
    prepare_build_directory()

    number_of_compiles = 0
    for path in _flatten_directory(config.LOC_BUILD):
        if '.moon' not in path: continue

        destination    = _change_extension(path, '.lua')
        moon_filename  = os.path.basename(path)
        lua_filename   = os.path.basename(destination)
        final_location = os.path.normpath(os.path.join(os.path.dirname(path), lua_filename))

        # If the file has not been modified, skip it.
        if not _file_is_new_or_modified(path):
            os.remove(path)
            continue

        log(0, f'Compiling file {moon_filename} to {lua_filename}')

        # Compile the file using the moonc executable.
        ok, error = run_external_tool([config.EXE_MOONC, '-o', final_location, path])
        if not ok:
            log(2, f'Unable to compile {moon_filename}. Reason:\n{error}')
            continue

        os.remove(path)
        number_of_compiles += 1

    if number_of_compiles <= 0:
        log(0, f'Nothing to do :)')


def clean_build_directory():
    global BUILD_DATA

    log(0, 'Cleaning build directory.')
    try:
        if os.path.exists(config.LOC_BUILD):
            shutil.rmtree(config.LOC_BUILD)
        BUILD_DATA.clear()
    except Exception as error:
        log(2, f'Unable to clean build directory. Reason: {error}')


def make_release():
    log(0, 'Making release.')


def run_build():
    log(0, 'Running build.')
    ok, error = run_external_tool([config.EXE_LOVE, config.LOC_BUILD])
    if not ok:
        log(2, f'Unable to run build. Reason: {error}')


def usage(executable_name):
    print(f'Usage: {executable_name} [help|build|release|run]')
    exit(0)

def log(type, status):
    type_name   = 'STATUS'
    should_exit = False

    if type == 1:
        type_name   = 'WARNING'
    elif type >= 2:
        type_name   = 'ERROR'
        should_exit = True

    print(f'[{type_name}]: {status}')
    if should_exit: exit(1)

def main(executable_name, argc, argv):
    global BUILD_DATA

    build_actions = {
        'Standard' : [default_build],
        'Run'      : [default_build, run_build],
        'Release'  : [clean_build_directory, default_build, make_release],
    }

    if argc <= 0:
        build_process = build_actions['Standard']
    else:
        if argv[0] in ('build', 'standard'):
            build_process = build_actions['Standard']
        elif argv[0] in ('release', 'distribute'):
            build_process = build_actions['Release']
        elif argv[0] in ('run', 'start'):
            build_process = build_actions['Run']
        elif argv[0] in ('clean'):
            clean_build_directory()
            exit(0)
        else:
            usage(executable_name)

    # Parse previous build data if it exists.
    try:
        if os.path.exists(config.LOC_LAST):
            with open(config.LOC_LAST, 'rb') as file_handle:
                BUILD_DATA = pickle.load(file_handle)
    except Exception as error:
        log(1, f'Unable to load previous build data! Reason: {error}')

    for sub_process in build_process:
        sub_process()

    # After the build process has completed,
    with open(config.LOC_LAST, 'wb') as file_handle:
        file_handle.write(pickle.dumps(BUILD_DATA))


if __name__ == '__main__':
    # Pass in argv without the executable name
    arguments       = sys.argv
    executable_name = arguments.pop(0)
    main(executable_name, len(arguments), arguments)
