from math import factorial


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
    xs_sorted = sorted(xs)
    n = len(xs)
    if n < 2:
        return False, 0.0
    h = xs_sorted[1] - xs_sorted[0]
    for i in range(2, n):
        if abs((xs_sorted[i] - xs_sorted[i - 1]) - h) > tol:
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


def stirling_interpolate(x0, xs, ys):
    equal, h = is_equally_spaced(xs)
    if not equal:
        raise ValueError("Стирлинг работает только при равном шаге")

    table_fin = finite_differences(ys)
    n = len(xs) - 1
    alpha = n // 2
    t = (x0 - xs[alpha]) / h

    s1 = ys[alpha]
    s2 = ys[alpha]

    prod1 = 1.0
    prod2 = 1.0
    fact = 1.0

    shifts = [0]
    for i in range(1, n + 1):
        shifts.extend([-i, i])
    shifts = shifts[:n]

    for k in range(1, n + 1):
        fact *= k
        shift = shifts[k - 1]

        prod1 *= t + shift
        prod2 *= t - shift

        idx_c = len(table_fin[k]) // 2
        delta_c = table_fin[k][idx_c]

        idx_s = idx_c - (1 - len(table_fin[k]) % 2)
        delta_s = table_fin[k][idx_s]

        s1 += prod1 * delta_c / fact
        s2 += prod2 * delta_s / fact

    return (s1 + s2) / 2, table_fin


def bessel_interpolate(x, xs, ys):
    equal, h = is_equally_spaced(xs)
    if not equal:
        raise ValueError("Бессель работает только при равном шаге")

    table_fin = finite_differences(ys)

    n = len(xs)
    m = n // 2 - 1

    t = (x - xs[m]) / h
    y = (ys[m] + ys[m + 1]) / 2 + (t - 0.5) * table_fin[1][m]

    even_coeff = t * (t - 1) / 2
    odd_coeff = (t - 0.5) * t * (t - 1) / 6

    r = 1
    while True:
        k_even = 2 * r
        k_odd = k_even + 1
        if k_even < len(table_fin):
            i_left = m - r
            i_right = i_left + 1
            if 0 <= i_left and i_right < len(table_fin[k_even]):
                y += even_coeff * (table_fin[k_even][i_left] + table_fin[k_even][i_right]) / 2
        if k_odd < len(table_fin):
            idx = m - r
            if 0 <= idx < len(table_fin[k_odd]):
                y += odd_coeff * table_fin[k_odd][idx]

        if (k_even >= len(table_fin) and k_odd >= len(table_fin)) or m - r - 1 < 0:
            break

        even_coeff *= (t + r) * (t - r - 1) / ((2 * r + 2) * (2 * r + 1))
        odd_coeff *= (t + r) * (t - r - 1) / ((2 * r + 3) * (2 * r + 2))
        r += 1

    return y, table_fin
