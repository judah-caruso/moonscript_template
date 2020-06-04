import os
import sys
import shutil
import pickle

from fnmatch import fnmatch
from platform import system, architecture
from subprocess import PIPE, Popen
from urllib.request import urlretrieve

import configuration as config # Edit 'configuration.py' to edit build settings

# Global variables for keeping track of the current build.
BUILD_DATA   = dict()
PLATFORM     = system()
ARCHITECTURE = architecture()[0]

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


# Checks if map has a case-insensitive match for value.
# Will match against keys and their values.
def _value_exists_in_map(map, value) -> (bool, str):
    lower_value = value.lower()

    for map_key, map_value in map.items():
        assert isinstance(map_value, str), 'Expected string value!'
        lower_map_key   = map_key.lower()
        lower_map_value = map_value.lower()

        if lower_value == lower_map_key or lower_value == lower_map_value:
            return (True, map_value)

    return (False, None)


def _make_platform_download_url(platform, architecture='') -> str:
    stem                  = f'https://github.com/love2d/love'
    download_uri          = f'releases/download/{config.VER_LOVE}'
    filetype              = 'zip'
    platform_release_name = 'win32'

    if platform == 'Windows':
        platform_release_name = 'win32'
        if architecture == 'x86_64':
            platform_release_name = 'win64'
    elif platform == 'Darwin':
        platform_release_name = 'macos'
    elif platform == 'Linux':
        filetype              = 'tar.gz'
        platform_release_name = 'linux-i686'
        if architecture == 'x86_64':
            platform_release_name = 'linux-x86_64'
    else:
        log(1, f'Unable to determine release for platform {platform}. Defaulting to {platform_release_name}')

    platform_version = f'love-{config.VER_LOVE}-{platform_release_name}.{filetype}'
    return f'{stem}/{download_uri}/{platform_version}'


def _download_release_for_platform(platform, architecture) -> (bool, str):
    log(0, f'Downloading Love2D {config.VER_LOVE} for {platform} ({architecture})')
    url = _make_platform_download_url(platform, architecture)

    try:
        if not os.path.exists(config.LOC_TEMP):
            os.mkdir(config.LOC_TEMP)

        _, extension = os.path.splitext(url)
        if platform == "Linux":
            extension = '.tar.gz'

        file_path = os.path.normpath(os.path.join(config.LOC_TEMP, f'love{extension}'))

        if os.path.exists(file_path):
            log(1, f'Love2D release already exists at {file_path}. Using that instead.')
            return (True, file_path)

        urlretrieve(url, file_path)
        return (True, file_path)
    except Exception as error:
        log(2, f'Error while downloading Love2D release. Reason: {error}')

    return (False, None)


def _unpack_release(file_path) -> str:
    try:
        shutil.unpack_archive(file_path, config.LOC_TEMP)
        extract_path = list(filter(lambda path: path not in file_path, os.listdir(config.LOC_TEMP)))

        if len(extract_path) > 0:
            return extract_path[0]

        raise Exception('Unable to find extracted folder.')
    except Exception as error:
        raise error


def _create_release_data(love_zip_path, platform, architecture):
    release_data            = dict()
    formatted_platform_name = f'{str(platform[:3]).lower()}_{architecture}'

    # The folder that gets created in temp when we unpack love.(zip/tar.gz).
    release_data['love_release_path']     = os.path.join(config.LOC_TEMP, _unpack_release(love_zip_path))
    release_data['platform_release_path'] = os.path.join(config.LOC_REL, os.path.join(platform, architecture))
    release_data['project_release_name']  = f'{config.VAL_NAME}_{config.VAL_REV.replace(".", "")}-{formatted_platform_name}'
    release_data['project_release_path']  = os.path.join(release_data['platform_release_path'], release_data['project_release_name'])
    release_data['build_archive_path']    = os.path.join(config.LOC_TEMP, config.VAL_NAME)
    release_data['love_file_path']        = f'{release_data["build_archive_path"]}.love'

    return release_data


def run_external_tool(command) -> (bool, str):
    if shutil.which(command[0]) == None:
        return (False, f'Unable to find executable {command[0]}')

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


def clean_build_directory():
    global BUILD_DATA

    log(0, 'Cleaning build directory.')
    try:
        if os.path.exists(config.LOC_BUILD):
            shutil.rmtree(config.LOC_BUILD)
        BUILD_DATA.clear()
    except Exception as error:
        log(2, f'Unable to clean build directory. Reason: {error}')


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


def release_for_darwin() -> (bool, str):
    log(2, f'Release process for {PLATFORM} ({ARCHITECTURE}) is not available yet, sorry!')
    return (False, None)


def release_for_linux(architecture='x86') -> (bool, str):
    log(2, f'Release process for {PLATFORM} ({ARCHITECTURE}) is not available yet, sorry!')
    return (False, None)


def release_for_windows(architecture='x86') -> (bool, str):
    ok, file_path = _download_release_for_platform(PLATFORM, architecture)
    if not ok:
        log(2, f'Unable to get Love2D {config.VER_LOVE} release for {PLATFORM} ({architecture})')

    log(0, f'Creating {PLATFORM} ({architecture}) release build.')
    try:
        data = _create_release_data(file_path, PLATFORM, architecture)

        # If a .love file already exists, delete it.
        if os.path.exists(data['love_file_path']):
            os.remove(data['love_file_path'])

        # Create a .love file using the build directory.
        shutil.make_archive(data['build_archive_path'], 'zip', config.LOC_BUILD)
        os.rename(f'{data["build_archive_path"]}.zip', data['love_file_path'])

        # Append the bytes of the .love file to love.exe
        with open(os.path.join(data['love_release_path'], 'love.exe'), 'ab') as love_exe:
            with open(data['love_file_path'], 'rb') as love_file:
                love_exe.write(love_file.read())

        # Create a new project release within 'LOC_REL.'
        if not os.path.exists(data['platform_release_path']):
            os.makedirs(data['platform_release_path'], exist_ok=True)

        # Copy files from the love release directory to the project release directory.
        def _copy_windows_tree(source, destination):
            files_to_keep = ['.dll', 'love.exe', 'license.txt']
            for file in files_to_keep:
                if file in source:
                    if file == 'love.exe':
                        destination = destination.replace('love.exe', f'{config.VAL_NAME}.exe')

                    shutil.copy2(source, destination)

        shutil.copytree(data['love_release_path'], data['project_release_path'], dirs_exist_ok=True, copy_function=_copy_windows_tree)

        # Create a project release zip file alongside the project release folder.
        shutil.make_archive(os.path.join(data['platform_release_path'], data['project_release_name']), 'zip', data['project_release_path'])

        # Cleanup temp directory
        shutil.rmtree(config.LOC_TEMP)
        return True, data['project_release_path']
    except Exception as error:
        log(2, f'Error while creating release. Reason: {error}')

    return False, None


def make_release():
    log(0, 'Starting release process.')
    success = False

    if PLATFORM == 'Windows':
        success, path = release_for_windows(ARCHITECTURE)
    elif PLATFORM == 'Darwin':
        success, path = release_for_darwin()
    elif PLATFORM == 'Linux':
        success, path = release_for_linux(ARCHITECTURE)
    else:
        log(2, f'Release unavailable for {PLATFORM} ({ARCHITECTURE}).')

    if not success:
        log(2, f'Unable to build release for {PLATFORM} ({ARCHITECTURE}).')

    log(0, f'Successfully created new release build: {path}')


def run_build():
    log(0, 'Running build.')
    ok, error = run_external_tool([config.EXE_LOVE, config.LOC_BUILD])
    if not ok:
        log(2, f'Unable to run build. Reason: {error}')


def usage(executable_name):
    print(f'Usage: {executable_name} [help|build|run|release [win|osx|linux] [32|64]]')
    exit(0)


def log(type, status, override_exit=False):
    type_name   = 'STATUS'
    should_exit = False

    if type == 1:
        type_name = 'WARNING'
    elif type >= 2:
        type_name   = 'ERROR'
        should_exit = True

    print(f'[{type_name}]: {status}')
    if override_exit:
        should_exit = not should_exit

    if should_exit: exit(1)


def main(executable_name, argc, argv):
    global BUILD_DATA, ARCHITECTURE, PLATFORM

    build_actions = {
        'Standard' : [default_build],
        'Run'      : [default_build, run_build],
        'Release'  : [clean_build_directory, default_build, make_release],
    }

    platform_map = {
        'win'   : 'Windows',
        'osx'   : 'Darwin',
        'linux' : 'Linux',
        '32'    : 'x86',
        '32bit' : 'x86',
        '64'    : 'x86_64',
        '64bit' : 'x86_64',
    }

    if argc <= 0:
        build_process = build_actions['Standard']
    else:
        flag = argv.pop(0)

        if flag in ('build', 'standard'):
            build_process = build_actions['Standard']
        elif flag in ('release', 'distribute'):
            if len(argv) > 0:
                # Verify and apply the target platform
                platform_wanted   = argv.pop(0).lower()
                ok, platform_name = _value_exists_in_map(platform_map, platform_wanted)
                if not ok:
                    log(2, f'Invalid platform selected {platform_wanted}', override_exit=True)
                    usage(executable_name)

                PLATFORM = platform_name

                # Verify and apply target architecture to platform. Default to x86 if not specified.
                if len(argv) > 0:
                    architecture = argv.pop(0).lower()

                    ok, architecture_name = _value_exists_in_map(platform_map, architecture)
                    if not ok:
                        log(2, f'Invalid architecture selected {architecture}', override_exit=True)
                        usage(executable_name)

                    ARCHITECTURE  = architecture_name
                else:
                    log(1, f'No architecture specified for {platform_name}. Defaulting to {ARCHITECTURE}.')

            else:
                _, PLATFORM     = _value_exists_in_map(platform_map, PLATFORM)
                _, ARCHITECTURE = _value_exists_in_map(platform_map, ARCHITECTURE)
                log(1, f'No release platform or architecture was selected. Defaulting to {PLATFORM} ({ARCHITECTURE}).')

            build_process = build_actions['Release']
        elif flag in ('run', 'start'):
            build_process = build_actions['Run']
        elif flag in ('clean'):
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
    # Pass argv in without the executable name
    arguments       = sys.argv[1:]
    executable_name = sys.argv[0]
    main(executable_name, len(arguments), arguments)
