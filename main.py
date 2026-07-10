from src.EasyFlowQ import start
from multiprocessing import freeze_support


if __name__ == "__main__":
    freeze_support()
    start.startGUI()