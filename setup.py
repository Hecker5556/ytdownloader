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

    import os
    pathtoexe = "ytdownload.exe"
    for root, dirs, files in os.walk('.'):
        if pathtoexe in files:
            filepath = os.path.abspath(root)
            break
    print(filepath)
    current_path = os.environ['PATH']
    new_path = f'{filepath}{os.pathsep}{current_path}'
    os.environ['PATH'] = new_path
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

