from typing import *

from PyQt5 import QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from functions import BUILTIN_FUNCTIONS

from util import load_csv

from methods import lagrange_interpolate, newton_finite, newton_divided


class NodeTableModel(QtCore.QAbstractTableModel):
    headers = ["x", "y"]

    def __init__(self, xs=None, ys=None):
        super().__init__()
        self.xs: List[float] = xs or []
        self.ys: List[float] = ys or []

    # --- Qt boilerplate ---
    def rowCount(self, _=QtCore.QModelIndex()):
        return len(self.xs)

    def columnCount(self, _=QtCore.QModelIndex()):
        return 2

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        r, c = index.row(), index.column()
        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return str(self.xs[r] if c == 0 else self.ys[r])
        return None

    def setData(self, index, value, role):
        if role != QtCore.Qt.EditRole:
            return False
        try:
            val = float(value.replace(",", "."))
        except Exception:
            return False
        r, c = index.row(), index.column()
        (self.xs if c == 0 else self.ys)[r] = val
        self.dataChanged.emit(index, index)
        return True

    def flags(self, _):
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable

    # helpers
    def insert_row(self, x=0.0, y=0.0):
        self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())
        self.xs.append(x)
        self.ys.append(y)
        self.endInsertRows()

    def clear(self):
        self.beginResetModel()
        self.xs.clear()
        self.ys.clear()
        self.endResetModel()


###############################################################################
# Главное окно                                                                #
###############################################################################

class InterpolationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ЛР № 5 – Интерполяция функции")
        self.resize(1024, 640)
        self.model = NodeTableModel()
        self._build_ui()

    # ------------------------- UI ---------------------------------------
    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        hbox = QtWidgets.QHBoxLayout(central)

        # Левый TabWidget (данные / параметры)
        tabs = QtWidgets.QTabWidget()
        hbox.addWidget(tabs, 0)

        # ---- TAB «Данные» -------------------------------------------------
        tab_data = QtWidgets.QWidget()
        tabs.addTab(tab_data, "Данные")
        v_data = QtWidgets.QVBoxLayout(tab_data)

        self.radio_manual = QtWidgets.QRadioButton("Таблица с клавиатуры")
        self.radio_file = QtWidgets.QRadioButton("CSV‑файл …")
        self.radio_func = QtWidgets.QRadioButton("Аналитическая функция")
        self.radio_manual.setChecked(True)
        for rb in (self.radio_manual, self.radio_file, self.radio_func):
            v_data.addWidget(rb)

        # таблица узлов
        tv = QtWidgets.QTableView()
        tv.setModel(self.model)
        tv.horizontalHeader().setStretchLastSection(True)
        v_data.addWidget(tv, 1)
        self.table_view = tv

        btns = QtWidgets.QHBoxLayout()
        v_data.addLayout(btns)
        btn_add = QtWidgets.QPushButton("+ узел")
        btn_del = QtWidgets.QPushButton("– узел")
        btns.addWidget(btn_add)
        btns.addWidget(btn_del)
        btn_add.clicked.connect(lambda: self.model.insert_row())
        btn_del.clicked.connect(self._delete_selected_row)

        # CSV / функция
        self.file_button = QtWidgets.QPushButton("Загрузить из файла …")
        v_data.addWidget(self.file_button)
        self.file_button.clicked.connect(self._load_csv_dialog)

        h_func = QtWidgets.QHBoxLayout()
        v_data.addLayout(h_func)
        self.func_combo = QtWidgets.QComboBox()
        self.func_combo.addItems(BUILTIN_FUNCTIONS.keys())
        self.func_a, self.func_b = QtWidgets.QLineEdit("0"), QtWidgets.QLineEdit("3.1416")
        self.func_n = QtWidgets.QSpinBox()
        self.func_n.setRange(2, 99)
        self.func_n.setValue(7)
        for w in (QtWidgets.QLabel("f(x):"), self.func_combo, QtWidgets.QLabel("a:"), self.func_a,
                  QtWidgets.QLabel("b:"), self.func_b, QtWidgets.QLabel("n:"), self.func_n):
            h_func.addWidget(w)

        # ---- TAB «Параметры» ---------------------------------------------
        tab_par = QtWidgets.QWidget()
        tabs.addTab(tab_par, "Параметры")
        v_par = QtWidgets.QVBoxLayout(tab_par)

        self.chk_lagr = QtWidgets.QCheckBox("Полином Лагранжа")
        self.chk_div = QtWidgets.QCheckBox("Полином Ньютона (разделённые)")
        self.chk_fin = QtWidgets.QCheckBox("Полином Ньютона (конечные)")
        self.chk_lagr.setChecked(True)
        for c in (self.chk_lagr, self.chk_div, self.chk_fin):
            v_par.addWidget(c)

        h_x0 = QtWidgets.QHBoxLayout()
        v_par.addLayout(h_x0)
        h_x0.addWidget(QtWidgets.QLabel("x₀:"))
        self.inp_x0 = QtWidgets.QLineEdit("0.5")
        h_x0.addWidget(self.inp_x0)

        self.btn_compute = QtWidgets.QPushButton("Вычислить")
        v_par.addWidget(self.btn_compute)
        self.btn_compute.clicked.connect(self._compute)

        self.results_edit = QtWidgets.QPlainTextEdit()
        self.results_edit.setReadOnly(True)
        v_par.addWidget(self.results_edit, 2)

        # новая таблица Δ              (пока пустая, скрыта)
        self.finite_table = QtWidgets.QTableWidget()
        self.finite_table.hide()
        self.finite_table.horizontalHeader().setStretchLastSection(True)
        self.finite_table.verticalHeader().setVisible(False)
        v_par.addWidget(self.finite_table, 3)

        # ---- График -------------------------------------------------------
        self.figure = Figure(figsize=(5, 4))
        self.canvas = FigureCanvas(self.figure)
        hbox.addWidget(self.canvas, 1)

    # ------------------------- helpers -----------------------------------
    def _delete_selected_row(self):
        sel = self.table_view.selectionModel().selectedRows()
        for i in sorted([s.row() for s in sel], reverse=True):
            self.model.beginRemoveRows(QtCore.QModelIndex(), i, i)
            del self.model.xs[i]
            del self.model.ys[i]
            self.model.endRemoveRows()

    def _load_csv_dialog(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "CSV …", "", "CSV (*.csv)")
        if not path:
            return
        try:
            xs, ys = load_csv(path)
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Ошибка чтения CSV", str(exc))
            return
        self.model.beginResetModel()
        self.model.xs, self.model.ys = xs, ys
        self.model.endResetModel()
        self.radio_file.setChecked(True)

    def _show_finite_table(self, xs: List[float], ys: List[float], table: List[List[float]]):
        n = len(xs)
        levels = len(table) - 1  # Δ^0 … Δ^levels
        headers = ["i", "xi", "yi"] + [f"Δ^{k}y" for k in range(1, levels + 1)]
        self.finite_table.setColumnCount(len(headers));
        self.finite_table.setRowCount(n)
        self.finite_table.setHorizontalHeaderLabels(headers)
        for i in range(n):
            self.finite_table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(i)))
            self.finite_table.setItem(i, 1, QtWidgets.QTableWidgetItem(f"{xs[i]:.5g}"))
            self.finite_table.setItem(i, 2, QtWidgets.QTableWidgetItem(f"{ys[i]:.5g}"))
        # остальные разности
        for k in range(1, levels + 1):
            col = 2 + k  # смещение от начала
            for i in range(n - k):  # на k‑м уровне на одну клетку меньше
                val = table[k][i]
                self.finite_table.setItem(i, col, QtWidgets.QTableWidgetItem(f"{val:.5g}"))
        # оформление
        self.finite_table.resizeColumnsToContents()
        self.finite_table.show()

    # -------------------------- core --------------------------------------
    def _collect_nodes(self):
        if self.radio_func.isChecked():
            try:
                a = float(self.func_a.text().replace(",", "."))
                b = float(self.func_b.text().replace(",", "."))
            except ValueError:
                raise ValueError("Некорректные границы интервала")
            if a >= b:
                raise ValueError("Требуется a < b")
            n = self.func_n.value()
            f = BUILTIN_FUNCTIONS[self.func_combo.currentText()]
            xs = [a + i * (b - a) / (n - 1) for i in range(n)]
            ys = [f(x) for x in xs]
            self.model.beginResetModel()
            self.model.xs, self.model.ys = xs, ys
            self.model.endResetModel()
        return self.model.xs, self.model.ys

    def _compute(self):
        try:
            xs, ys = self._collect_nodes()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Ошибка", str(e))
            return
        if len(xs) < 2:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Нужно минимум 2 узла интерполяции");
            return
        try:
            x0 = float(self.inp_x0.text().replace(",", "."))
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Некорректное значение x₀")
            return

        results, curves = [], []
        self.finite_table.hide()

        # Лагранж -----------------------------------------------------------
        if self.chk_lagr.isChecked():
            y_l = lagrange_interpolate(x0, xs, ys)
            results.append(f"Лагранж: y({x0}) ≈ {y_l:.10g}")
            curves.append(("Лагранж", lambda t, xs=xs, ys=ys: lagrange_interpolate(t, xs, ys)))

        # Ньютон / разделённые ---------------------------------------------
        if self.chk_div.isChecked():
            y_d, tbl_d = newton_divided(x0, xs, ys)
            results.append(f"Ньютон (разделённые): y({x0}) ≈ {y_d:.10g}")
            curves.append(("Ньютон (разделённые)", lambda t, xs=xs, ys=ys: newton_divided(t, xs, ys)[0]))

        # Ньютон / конечные -----------------------------------------------
        if self.chk_fin.isChecked():
            try:
                y_f, table_fin, form = newton_finite(x0, xs, ys)
                results.append(f"Ньютон (конечные, {form}): y({x0}) ≈ {y_f:.10g}")
                curves.append((f"Ньютон конечные ({form})", lambda t, xs=xs, ys=ys, f=form: (
                    newton_finite(t, xs, ys)[0])))
                self._show_finite_table(xs, ys, table_fin)
            except ValueError:
                results.append("⚠ Ньютон (конечные): узлы неравномерны, пропуск…")

        self.results_edit.setPlainText("\n".join(results))

        # ---------- график -------------------------------------------------
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_title("Интерполяция функции")
        ax.grid(True, linestyle=":", linewidth=0.5)
        ax.scatter(xs, ys, color="black", label="узлы")
        if self.radio_func.isChecked():
            f = BUILTIN_FUNCTIONS[self.func_combo.currentText()]
            xx = self._linspace(min(xs), max(xs), 200)
            ax.plot(xx, [f(t) for t in xx], label="f(x)")
        colors = ["red", "green", "blue", "orange"]
        for i, (lbl, fn) in enumerate(curves):
            xx = self._linspace(min(xs), max(xs), 400)
            ax.plot(xx, [fn(t) for t in xx], label=lbl, linewidth=1.1, color=colors[i % len(colors)])
        ax.legend(loc="best")
        self.canvas.draw()

    @staticmethod
    def _linspace(a: float, b: float, n: int):
        if n < 2:
            return [a]
        step = (b - a) / (n - 1)
        return [a + i * step for i in range(n)]
