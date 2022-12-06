from PyInstaller.utils.hooks import collect_all
from src.helpers import PATHSEP

def hook(hook_api):
    packages = [
        f"src{PATHSEP}messagehandler.py",
        f"src{PATHSEP}webconnector.py",
        f"src{PATHSEP}htmlparser.py",
        f"src{PATHSEP}album.py",
        f"src{PATHSEP}messages.py",
        f"src{PATHSEP}helpers.py",
    ]
    for package in packages:
        datas, binaries, hiddenimports = collect_all(package)
        hook_api.add_datas(datas)
        hook_api.add_binaries(binaries)
        hook_api.add_imports(*hiddenimports)