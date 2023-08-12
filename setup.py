def main():
    subprocess.run('pip install -r requirements.txt'.split())

    from cx_Freeze import setup, Executable

    build_options = {'packages': [], 'excludes': [], 'add_to_path': True}

    base = 'console'

    executables = [
        Executable('ytdownload.py', base=base)
    ]

    setup(name='ytdownloader',
        version = '1.0',
        description = 'downloads youtube videos',
        options = {'build_exe': build_options},
        executables = executables)

    import os, sys
    pathtoexe = "ytdownload.exe"
    for root, dirs, files in os.walk('.'):
        if pathtoexe in files:
            filepath = os.path.abspath(root)
            break
    if sys.platform.startswith('win'):
        import winreg

        def add_to_path(directory, user=False):
            if user:
                key = winreg.HKEY_CURRENT_USER
                subkey = 'Environment'
            else:
                key = winreg.HKEY_LOCAL_MACHINE
                subkey = r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'

            with winreg.OpenKey(key, subkey, 0, winreg.KEY_ALL_ACCESS) as regkey:
                path_value, _ = winreg.QueryValueEx(regkey, 'Path')
                print(path_value)
                path_value += ';' + directory
                winreg.SetValueEx(regkey, 'Path', 0, winreg.REG_EXPAND_SZ, path_value)

        # Example usage
        directory_path = filepath

        # Add to system PATH
        add_to_path(directory_path)
    elif sys.platform.startswith('linux'):
        homedirectory = os.path.expanduser('~')
        profilefile = os.path.join(homedirectory, '.bashrc')
        with open(profilefile, 'a') as f1:
            f1.write(f'\nexport PATH="$PATH:{filepath}"\n')
    input('\npress enter to exit\n')
if __name__ == '__main__':
    import subprocess
    subprocess.run('pip install pyuac'.split())
    subprocess.run('pip install pypiwin32'.split())
    #require admin to make sure modules are installed correctly
    import pyuac 

    if not pyuac.isUserAdmin():
        pyuac.runAsAdmin()
    else:
        main()

