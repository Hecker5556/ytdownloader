import asyncio, sys, os, traceback
async def get_pyuac():
    process = await asyncio.subprocess.create_subprocess_exec("pip", *['install', 'pyuac', 'pypiwin32', 'win32security', 'cx_freeze'])
    await process.wait()
async def windo():
    process = await asyncio.subprocess.create_subprocess_exec("pip", *["install", "-r", "requirements.txt"])
    await process.wait()
    from cx_Freeze import setup, Executable
    import winreg

    build_options = {'packages': [], 'excludes': []}

    base = 'console'

    executables = [
        Executable('ytdownload.py', base=base)
    ]

    setup(name='ytdownloader',
        version = '2.0',
        description = 'downloads youtube videos',
        options = {'build_exe': build_options},
        executables = executables)
    for root, dirs, files in os.walk('.'):
        if "ytdownload.exe" in files:
            directory = os.path.abspath(root)
            break
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
async def linu():
    if not os.path.exists("ytdownloader.py"):
        filepath = str(input("path to ytdownloader.py: "))
    else:
        filepath = os.path.abspath("ytdownloader.py")
    process = await asyncio.subprocess.create_subprocess_exec("pip", *["install", "-r", os.path.dirname(filepath) + 'requirements.txt'])
    await process.wait()
    with open("~/.bash_profile", "a") as f1:
        f1.write(f"\nexport PATH=$PATH:{filepath}")
    process = await asyncio.subprocess.create_subprocess_exec("source", *["~/.bash_profile"])
    await process.wait()
    process = await asyncio.subprocess.create_subprocess_exec("chmod", *["+x", filepath])
    await process.wait()
if __name__ == "__main__":
    if sys.platform.startswith("win"):
        try:
            import pyuac
        except ModuleNotFoundError:
            asyncio.run(get_pyuac())
        try:
            import cx_Freeze
        except ModuleNotFoundError:
            asyncio.run(get_pyuac())
        import pyuac
        if not pyuac.isUserAdmin():
            pyuac.runAsAdmin()
            sys.exit()
        else:
            try:
                asyncio.run(windo())
            except Exception as e:
                traceback.print_exc()
    else:
        if os.getuid() != 0:
            raise RuntimeError("run as sudo")
        asyncio.run(linu())
