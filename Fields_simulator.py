from Interface_manager import Interfacemanager_class
from UI_manager import UI_Manager_class
import sys

def main():
    if len(sys.argv) == 2:
        if sys.argv[1] == "-cli":
            ui = Interfacemanager_class()
            ui.start()
    else:
        ui = UI_Manager_class()
        ui.start()

if __name__ == "__main__":
    main()
