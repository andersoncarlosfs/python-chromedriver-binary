# coding: utf-8
"""
Helper functions for filename and URL generation.
"""

import sys
import os
import ssl
import subprocess
import re
import platform
import array
import ctypes

try:
    from urllib.request import urlopen, URLError
    ssl_context = ssl.SSLContext()
except ImportError:
    from urllib2 import urlopen, URLError
    ssl_context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS)

__author__ = 'Daniel Kaiser <d.kasier@fz-juelich.de>'


def get_chromedriver_filename():
    """
    Returns the filename of the binary for the current platform.
    :return: Binary filename
    """
    if sys.platform.startswith('win'):
        return 'chromedriver.exe'
    return 'chromedriver'


def get_variable_separator():
    """
    Returns the environment variable separator for the current platform.
    :return: Environment variable separator
    """
    if sys.platform.startswith('win'):
        return ';'
    return ':'


def get_chromedriver_url(version):
    """
    Generates the download URL for current platform , architecture and the given version.
    Supports Linux, MacOS and Windows.
    :param version: chromedriver version string
    :return: Download URL for chromedriver
    """
    base_url = 'https://chromedriver.storage.googleapis.com/'
    if sys.platform.startswith('linux') and sys.maxsize > 2 ** 32:
        _platform = 'linux'
        architecture = '64'
    elif sys.platform == 'darwin':
        _platform = 'mac'
        architecture = '64'
        if platform.machine() == 'arm64':
            if int(version.split('.')[0]) < 107:
                architecture += '_m1'
            else:
                architecture = '_arm64'
    elif sys.platform.startswith('win'):
        _platform = 'win'
        architecture = '32'
    else:
        raise RuntimeError('Could not determine chromedriver download URL for this platform.')
    return base_url + version + '/chromedriver_' + _platform + architecture + '.zip'


def find_binary_in_path(filename):
    """
    Searches for a binary named `filename` in the current PATH. If an executable is found, its absolute path is returned
    else None.
    :param filename: Filename of the binary
    :return: Absolute path or None
    """
    if 'PATH' not in os.environ:
        return None
    for directory in os.environ['PATH'].split(get_variable_separator()):
        binary = os.path.abspath(os.path.join(directory, filename))
        if os.path.isfile(binary) and os.access(binary, os.X_OK):
            return binary
    return None


def get_latest_release_for_version(version=None):
    """
    Searches for the latest release (complete version string) for a given major `version`. If `version` is None
    the latest release is returned.
    :param version: Major version number or None
    :return: Latest release for given version
    """
    release_url = "https://chromedriver.storage.googleapis.com/LATEST_RELEASE"
    if version:
        release_url += '_{}'.format(version)
    try:
        response = urlopen(release_url, context=ssl_context)
        if response.getcode() != 200:
            raise URLError('Not Found')
        return response.read().decode('utf-8').strip()
    except URLError:
        raise RuntimeError('Failed to find release information: {}'.format(release_url))


def get_chrome_major_version():
    """
    Detects the major version number of the installed chrome/chromium browser.
    :return: The browsers major version number or None
    """
    browser_executables = ['google-chrome', 'chrome', 'chrome-browser', 'google-chrome-stable', 'chromium', 'chromium-browser']
    if sys.platform == "darwin":
        browser_executables.insert(0, "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

    get_major_version = lambda version: re.match(r'.*?((?P<major>\d+)\.(\d+\.){2,3}\d+).*?', version).group('major')

    for browser_executable in browser_executables:
        try:
            version = subprocess.check_output([browser_executable, '--version'])
            
            return get_major_version(version.decode('utf-8'))
        
        except Exception:
            if sys.platform.startswith('win') or sys.platform.startswith('cygwin'):
                try:
                    import winreg
                    with winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon") as key:
                        version = winreg.QueryValueEx(key, "version")[0]

                        return get_major_version(version)
                
                except Exception:
                    roots = list(filter(None, [os.getenv('LocalAppData'), os.getenv('ProgramFiles'), os.getenv('ProgramFiles(x86)'), os.getenv('ProgramW6432')]))
                
                    for root in roots:
                        try:
                            # https://stackoverflow.com/questions/580924/how-to-access-a-files-properties-on-windows
                            document = os.path.join(root, 'Google', 'Chrome', 'Application', browser_executable + '.exe')
                            
                            name = document.replace(os.path.sep, f'{os.path.sep}{os.path.sep}')
                            
                            version = subprocess.check_output(['wmic', 'datafile', 'where', f'name="{name}"', 'get', 'Version', '/value'])
                            
                            return get_major_version(version.decode('utf-8').strip())
                        
                        except Exception:
                            pass
            pass

def check_version(binary, required_version):
    try:
        version = subprocess.check_output([binary, '-v'])
        version = re.match(r'.*?([\d.]+).*?', version.decode('utf-8'))[1]
        if version == required_version:
            return True
    except Exception:
        return False
    return False


def get_chromedriver_path():
    """
    :return: path of the chromedriver binary
    """
    return os.path.abspath(os.path.dirname(__file__))


def print_chromedriver_path():
    """
    Print the path of the chromedriver binary.
    """
    print(get_chromedriver_path())
