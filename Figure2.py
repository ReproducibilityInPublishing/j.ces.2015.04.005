import csv
import matplotlib.pyplot as plt
import numpy as np

# Read analytic data from file.
x_analytic = []
y_analytic = []
last_y = -1.
with open("Case5_n_analytic.csv", "r") as analytic_file:
    csvreader = csv.reader(analytic_file, delimiter=",", quotechar='"')
    for row in csvreader:
        x = float(row[0])
        y = float(row[1])
        if y != last_y:
            x_analytic.append(x)
            y_analytic.append(y)
            last_y = y

x_analytic.append(10.)
y_analytic.append(y_analytic[-1])

x_analytic = np.array(x_analytic)
y_analytic = np.array(y_analytic)

# Produce Figures 1a-d
plt.figure(1, figsize=(12,8), dpi=80)

node_num_list = [1, 2, 3, 4]

for node_num in node_num_list:
    plt.subplot(220+node_num)

    plt.plot([], color="#0A246A", linestyle="-", label="Analytical solution")

    plt.plot(x_analytic, y_analytic, color="#0A246A", linestyle="-")

    plt.legend()
    plt.ylabel(r"$n(\xi)$")
    plt.xlabel(r"$\xi$")
    plt.xlim(1., 10.)
    plt.ylim(0., 1.)

plt.subplots_adjust(left=0.11, right = 0.98, bottom=0.1, top=0.95, wspace=0.2, hspace = 0.15)

plt.savefig("Figure2.png")