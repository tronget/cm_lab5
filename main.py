import sys
from PyQt5 import QtWidgets
from UI import InterpolationWindow


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = InterpolationWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
