import csv


def load_csv(path: str):
    xs, ys = [], []
    with open(path, newline="", encoding="utf-8-sig") as fp:
        reader = csv.reader(fp, delimiter=";", skipinitialspace=True)
        for row in reader:
            if len(row) < 2:
                continue
            try:
                xs.append(float(row[0].replace(",", ".")))
                ys.append(float(row[1].replace(",", ".")))
            except ValueError:
                continue
    return xs, ys
