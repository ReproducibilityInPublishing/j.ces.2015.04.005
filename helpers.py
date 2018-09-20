import math
import csv
import subprocess
import re
import scipy.integrate as integrate
import scipy.special as special
from shutil import copyfile

def load_probe_data(filepath):
    data_dict = {}
    with open(filepath, "r") as filedata:
        lines = filedata.readlines()
    for line in lines:
        if line[0] == "#":
            continue
        components = line.split()
        try:
            x = float(components[0])
            y = float(components[1])
            data_dict[x] = y
        except:
            pass
    return data_dict

def load_csv_data(filepath):
    data_dict = {}
    with open(filepath, "r") as analytic_file:
        csvreader = csv.reader(analytic_file, delimiter=",", quotechar='"')
        for row in csvreader:
            x = float(row[0])
            y = float(row[1])
            data_dict[x] = y
    return data_dict

def lognormal_moment(k, mu, sigma):
    return math.exp((k*mu)+(k*k*sigma*sigma/2))

def gamma_moment(k, mu, sigma):
    Lambda = mu/sigma
    return (math.gamma(Lambda+k)/math.gamma(Lambda))*(mu/Lambda)**k

def lognormal_analytic_moment(k, mu1, sigma1, mu2, sigma2):
    return (lognormal_moment(k, mu1, sigma1)+lognormal_moment(k, mu2, sigma2))/2.

def lognormal_kern(x, mu, sigma):
    return math.exp(-(math.log(x)-mu)**2/(2*sigma**2))/(x*sigma*math.sqrt(2*math.pi))

def gamma_kern(x, mu, sigma):
    Lambda = mu/sigma
    try:
        return (((x**(Lambda-1))*math.exp(-x/sigma))/(math.gamma(Lambda)*(sigma**Lambda)))
    except OverflowError:
        try:
            log_kern = (Lambda-1)*math.log(x)-(x/sigma)-special.loggamma(Lambda)-Lambda*math.log(sigma)
            return math.exp(log_kern)
        except OverflowError as e:
            print("x: ", x)
            print("mu: ", mu)
            print("sigma: ", sigma)
            print("Lambda: ", Lambda)
            raise e


def f_lognormal(x, mu1, sigma1, mu2, sigma2):
    return (lognormal_kern(x, mu1, sigma1)+lognormal_kern(x, mu2, sigma2))/2.

def f_num_lognormal(x, node_definitions):
    value = 0
    for i in range(0,node_definitions['n']):
        value += node_definitions[i]['w']*lognormal_kern(x, node_definitions[i]['ab'], node_definitions['sig'])
    return value

def f_num_gamma(x, node_definitions):
    value = 0
    for i in range(0,node_definitions['n']):
        value += node_definitions[i]['w']*gamma_kern(x, node_definitions[i]['ab'], node_definitions['sig'])
    return value

def f_num_single_lognormal(x, node_definitions, i):
    return node_definitions[i]['w']*lognormal_kern(x, node_definitions[i]['ab'], node_definitions['sig'])

def f_num_single_gamma(x, node_definitions, i):
    return node_definitions[i]['w']*gamma_kern(x, node_definitions[i]['ab'], node_definitions['sig'])

def l2diff(f_func, p_func, xmin, xmax, N):
    dx = (xmax-xmin)/N
    summation = 0.
    for i in range(0, N):
        x = xmin+(dx*i)
        summation += (f_func(x)-p_func(x))**2

    summation = math.sqrt(summation*dx)
    return summation

def log_coalescence_ndf(t, xi, loud=False):
    if loud:
        print(special.iv(1, 2*xi*math.sqrt(1-math.exp(-t))))
    return -t-2*xi+xi*math.exp(-t)-math.log(xi)-(1/2)*(1-math.exp(-t))+math.log(special.iv(1, 2*xi*math.sqrt(1-math.exp(-t))))

def coalescence_ndf(t, xi):
    #return math.exp(log_coalescence_ndf(t,xi))
    return (math.exp(-t-2*xi+xi*math.exp(-t))/(xi*math.sqrt(1-math.exp(-t))))*special.iv(1,2*xi*math.sqrt(1-math.exp(-t)))


def condensation_ndf(t, xi):
    return ((xi*math.exp(-t/2))**3*math.exp(-xi*math.exp(-t/2)))/(6*math.exp(t/2))

def extract_analytic_moment(f, xmin, xmax, N):
    # We are explicitly ignoring error here!!
    return integrate.quad(lambda x: (x**N)*f(x), xmin, xmax)[0]

sigma_re = re.compile("Sigma = (\d*\.\d*)")
node_re = re.compile("Primary node (\d*)")
weight_re = re.compile("Primary weight = (\d*\.\d*)")
absicca_re = re.compile("Primary abscissa = (\d*\.\d*)")

def perform_moment_inversion(node_num, analytic_moments, inversion_type='lognormal'):
    # Prepare moment inversion for the appropriate type.    
    copyfile('quadratureProperties.{}'.format(inversion_type), 'quadratureProperties')

    node_definitions = {'n': node_num}

    # Build command
    command = ["Test-ExtendedMomentInversion", str(2*node_num+1)]
    for i in range(0, 2*node_num+1):
        command.append(str(analytic_moments[i]))

    # Run command
    output_lines = subprocess.check_output(command)
    found_sigma = False
    for line in output_lines.splitlines():
        str_line = line.decode("utf-8")
        sigma_match = sigma_re.match(str_line)
        if sigma_match:
            node_definitions['sig'] = float(sigma_match.group(1))
            found_sigma = True
    if not found_sigma:
        print("Couldn't get sigma!!")
        sys.exit(-1)

    # Extract weight, and abscissae information 
    with open('secondaryQuadrature', 'r') as quad_file:
        quadrature_lines = quad_file.readlines()

    # split lines by node
    current_node = -1
    temp_info = {}
    for line in quadrature_lines:
        node_match = node_re.match(line)
        if node_match:
            if current_node != -1:
                node_definitions[current_node] = temp_info
            current_node = int(node_match.group(1))
            temp_info = {}
        weight_match = weight_re.match(line)
        if weight_match:
            temp_info['w'] = float(weight_match.group(1))
        absicca_match = absicca_re.match(line)
        if absicca_match:
            if inversion_type == 'lognormal':
                temp_info['ab'] = math.log(float(absicca_match.group(1)))
            else:
                temp_info['ab'] = float(absicca_match.group(1))
    if current_node != -1:
        node_definitions[current_node] = temp_info

    return node_definitions
