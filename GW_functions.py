from pynput import mouse
import math
import csv
import os

CALIBRE_FILE = "calibre.csv"


def main():
    while True :
        try :
            menu = int(input("""for launching game enter 1
for calibrating coordinates enter 2
"""))
        except ValueError :
            print("please enter either 1 or 2")
        else:
            if menu == 1:
                run_game()
                break
            elif menu == 2:
                callibre()
                print("Calibration saved.")
            else:
                print("Invalid choice.")



def run_game():
    if os.path.exists(CALIBRE_FILE):
        a1, b1, a2, b2 = load_calibre()
    else:
        print("No calibration found, let's calibrate first.")
        a1, b1, a2, b2 = callibre()

    x = []
    y = []
    number_of_points = int(input("how many points to pass through: ")) + 1
    points = get_n_clicks(number_of_points)
    for i in range(len(points)):
        x.append(((points[i][0] - a1) * (25 / b1)))
        y.append((-15 / b2) * (points[i][1] - a2))

    print(f"""
    Lagrange polynomial :{written_polynomial(interpolation(x,y))}
    Gauss summation :{gaussian(x,y)}
    Cornered sigmoids summation :{cornered_sigmoids(x,y)}""")


def callibre():
    print("""Please ALT+TAB into any Graphwar game and click respectivly (25,0) and (0,15) 
Be as precise a possible""")
    cal = get_n_clicks(2)
    a1 = cal[1][0]
    b1 = cal[0][0] - a1
    a2 = cal[0][1]
    b2 = a2 - cal[1][1]

    with open(CALIBRE_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["a1", "b1", "a2", "b2"])
        writer.writerow([a1, b1, a2, b2])

    return [a1, b1, a2, b2]


def load_calibre():
    with open(CALIBRE_FILE, newline="") as f:
        reader = csv.DictReader(f)
        row = next(reader)
        return float(row["a1"]), float(row["b1"]), float(row["a2"]), float(row["b2"])


def get_n_clicks(n):
    points = []
    def on_click(x, y, button, pressed):
        if pressed:
            points.append([x, y])
            print(f"Point {len(points)}/{n} : ({x}, {y})")
            if len(points) >= n:
                return False
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()
    return points

def interpolation(x,y):
    n = len(x)
    l = []
    polf = []
    for i in range(n):
        interpolation = []
        produit_denominateurs = 1
        for j in range(n):
            if j == i:
                continue
            produit_denominateurs *= x[i] - x[j]
            interpolation.append(x[j])
        interpolation.append(produit_denominateurs)
        l.append(interpolation)
    for yi in range(len(y)):
        l[yi][-1] = float(y[yi] / l[yi][-1])
    for pol in l:
        if pol[-1] == 0:
            continue
        polf.append(pol)
    return polf

def written_polynomial(polf):
    if not polf :
        return "0"
    terms = []
    for i in range(len(polf)):
        facteurs = "*".join(f"(x-{polf[i][j]:.2f})" for j in range(len(polf[i]) - 1))
        terms.append(f"({to_sci_str(polf[i][-1])})*{facteurs}")
    polynome = "+".join(terms)
    polynome = polynome.replace("--", "+")
    return polynome

def gaussian(x,y) :
    gauss = "+".join(f"{y[i + 1] - y[0]:.3f}*exp(-(10(x-{x[i + 1]:.3f}))^2)" for i in range(len(x) - 1))
    gauss = gauss.replace("+-", "-")
    gauss = gauss.replace("--", "-")
    return gauss

def cornered_sigmoids(x,y):
    som = " "
    for i in range(len(y)-1):
        h = y[i + 1] - y[i]
        som = som + f" +{h:.4f}/(1+exp(-50(x-{(x[i + 1]):.4f})))"
    som = som.replace("+-", "-")
    som = som.replace("--", "+")
    return som

def to_sci_str(val, precision=3):
    if val == 0:
        return "0"
    exp = math.floor(math.log10(abs(val)))
    mantissa = val / (10 ** exp)
    return f"{mantissa:.{precision}f}*10^({exp})"

if __name__ == "__main__" :
    main()
