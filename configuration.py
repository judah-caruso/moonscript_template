LOC_SRC   = 'source'                # Relative location of .moon files.
LOC_LIB   = 'thirdparty'            # Relative location of .lua files.
LOC_RES   = 'assets'                # Relative location of asset files.
LOC_REL   = 'releases'              # Relative location for releases.
LOC_BUILD = '_build'                # Relative location for main build files.
LOC_TEMP  = '_temp'                 # Relative location for temporary release files.
LOC_LAST  = f'{LOC_BUILD}/last.pck' # Relative location for the build database file.

VAL_NAME  = 'Project'               # Name of the project.
VAL_REV   = '0.0.2'                 # Build revision (version) of the project.

# External build tools.
# If the executable is in your PATH, simply put the executable name.
# Otherwise, put the full path (e.g. r'C:\path\to\moonc.exe').
EXE_MOONC = 'moonc'                 # MoonScript compiler location.
EXE_LOVE  = 'love'                  # Love2D executable location.

VER_LOVE  = '11.3'                  # Version of Love2D to use for releases (follows the tag format on GitHub)

# Relative filenames or directories to ignore when building.
IGNORE = {
    'SRC': [],
    'LIB': ['.git', 'PLACE_LIBRARIES_HERE'],
    'RES': ['.git', 'PLACE_ASSETS_HERE'],
}
