from src.helpers import PATHSEP
import PyInstaller.__main__

PyInstaller.__main__.run([
    f"src{PATHSEP}userinterface.py",
    "--onefile", 
    "--noconfirm",
    f"-p=src{PATHSEP}",
    "--additional-hooks-dir=.",
    "-n RealBandcampMusicDiscovery",
    "--clean"
])