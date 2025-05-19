def lagrange_interpolate(x, xs, ys):
    n = len(xs)
    res = 0.0
    for i in range(n):
        term = ys[i]
        for j in range(n):
            if i != j:
                denom = xs[i] - xs[j]
                if denom == 0:
                    raise ZeroDivisionError("Повторяющиеся узлы интерполяции")
                term *= (x - xs[j]) / denom
        res += term
    return res


def divided_differences(xs, ys):
    n = len(xs)
    table = [ys.copy()]
    for lvl in range(1, n):
        prev = table[-1]
        curr = []
        for i in range(n - lvl):
            denom = xs[i + lvl] - xs[i]
            if denom == 0:
                raise ZeroDivisionError("Повторяющиеся узлы интерполяции")
            curr.append((prev[i + 1] - prev[i]) / denom)
        table.append(curr)
    return table


def newton_divided(x, xs, ys):
    table = divided_differences(xs, ys)
    res = table[0][0]
    prod = 1.0
    for lvl in range(1, len(xs)):
        prod *= (x - xs[lvl - 1])
        res += table[lvl][0] * prod
    return res, table


def finite_differences(ys):
    table = [ys.copy()]
    while len(table[-1]) > 1:
        prev = table[-1]
        lst = []
        for i in range(len(prev) - 1):
            lst.append(prev[i + 1] - prev[i])
        table.append(lst)
    return table


def is_equally_spaced(xs, tol=1e-9):
    if len(xs) < 2:
        return False, 0.0
    h = xs[1] - xs[0]
    for i in range(2, len(xs)):
        if abs((xs[i] - xs[i - 1]) - h) > tol:
            return False, h
    return True, h


def newton_forward(x, xs, ys, h):
    table = finite_differences(ys)
    t = (x - xs[0]) / h
    res = ys[0]
    prod = 1.0
    fact = 1
    for k in range(1, len(xs)):
        prod *= (t - (k - 1))
        fact *= k
        res += (prod / fact) * table[k][0]
    return res, table


def newton_backward(x, xs, ys, h):
    table = finite_differences(ys)
    t = (x - xs[-1]) / h
    res = ys[-1]
    prod = 1.0
    fact = 1
    for k in range(1, len(xs)):
        prod *= (t + (k - 1))
        fact *= k
        res += (prod / fact) * table[k][-1]
    return res, table


def newton_finite(x, xs, ys):
    eq, h = is_equally_spaced(xs)
    if not eq:
        raise ValueError("Нерегулярная сетка для конечных разностей")

    if abs(x - xs[0]) <= abs(x - xs[-1]):  # вперёд
        y_f, table_fin = newton_forward(x, xs, ys, h)
        form = "вперёд"
    else:
        y_f, table_fin = newton_backward(x, xs, ys, h)
        form = "назад"

    return y_f, table_fin, form
