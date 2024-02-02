def main():
    import os, subprocess
    requirements_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ytdownloader", "requirements.txt")
    subprocess.run(['pip', 'install', '-r', requirements_path])
    if sys.platform.startswith('win'):
        
        from cx_Freeze import setup, Executable

        build_options = {'packages': [], 'excludes': []}

        base = 'console'

        executables = [
            Executable('ytdownload.py', base=base)
        ]

        setup(name='ytdownloader',
            version = '1.0',
            description = 'downloads youtube videos',
            options = {'build_exe': build_options},
            executables = executables)

        pathtoexe = "ytdownload.exe"
        for root, dirs, files in os.walk('.'):
            if pathtoexe in files:
                filepath = os.path.abspath(root)
                break

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
                if directory not in path_value:
                    path_value += ';' + directory
                    winreg.SetValueEx(regkey, 'Path', 0, winreg.REG_EXPAND_SZ, path_value)
                else:
                    print(f'{directory} is already in path:\n{path_value}')

        directory_path = filepath

        add_to_path(directory_path)
    elif sys.platform.startswith('linux'):
        #cant build to exe on linux
        pathtopy = "ytdownload.py"
        for root, dirs, files in os.walk('.'):
            if pathtopy in files:
                filepath = os.path.abspath(root)
                break
        with open(os.path.join(filepath, pathtopy), 'r') as f1:
            script = f1.read()
        with open(os.path.join(filepath, pathtopy), 'w') as f1:
            f1.write('#!/usr/bin/env python\n' + script)
        homedirectory = os.path.expanduser('~')
        profilefile = os.path.join(homedirectory, '.bashrc')
        print(os.path.abspath(profilefile))
        with open(profilefile, 'a') as f1:
            f1.write(f'\nexport PATH="$PATH:{filepath}"\n')
        print(f'usage: {filepath + "/ytdownload.py"} to execute')
        with open('usagecommand.txt', 'w') as f1:
            f1.write(f'{filepath + "/ytdownload.py"}')
        subprocess.run(f'chmod +x {filepath + "/ytdownload.py"}'.split())
        
       
if __name__ == '__main__':
    import subprocess, sys, os
    if sys.platform.startswith('win'):
        subprocess.run('pip install pyuac'.split())
        subprocess.run('pip install pypiwin32'.split())
        subprocess.run('pip install win32security'.split())
        subprocess.run('pip install cx_Freeze'.split())
        #require admin to make sure modules are installed correctly
        import pyuac 

        if not pyuac.isUserAdmin():
            pyuac.runAsAdmin()
        else:
            try:
                sys.setrecursionlimit(5000)
                main()
                input("press enter to exit")
            except Exception as e:
                print(e)
                input("press enter to exit")
    elif sys.platform.startswith('linux'):
        if os.getuid() != 0:
            print('run as admin! (sudo)')
        else:
            main()
        
