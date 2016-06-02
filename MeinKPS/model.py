#! /usr/bin/python



"""
================================================================================
Title:    model

Author:   David Leclerc

Version:  0.1

Date:     02.06.2016

License:  GNU General Public License, Version 3
          (http://www.gnu.org/licenses/gpl.html)

Overview: ...

Notes:    ...
================================================================================
"""



# TERMINOLOGY
#   - IAC: insulin action curve
#   - PIA: peak of insulin action
#   - DIA: duration of insulin action



# LIBRARIES
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import scipy.optimize



def integrateSimpson(f, p, a, b, N):

    """
    This is a module that approximates the integral i of a given function f from
    a to b. In order to do that, it uses the Simpson method, with N intervals.
    """

    t = np.linspace(a, b, N, False)
    h = (b - a) / float(N)
    i = np.sum((f(t, p) + 4 * f(t + h/2, p) + f(t + h, p)) * h/6)

    #print ("Integral of IAC from a = " + str(a) + " to b = " + str(b) +
    #       " is " + str(i) + ".")

    return i



def generateIAC(t, p):

    """
    ============================================================================
    GENERATEIAC
    ============================================================================
    """

    a = p[0]
    b = p[1]
    c = p[2]

    IAC = a * t**b * np.exp(-c * t)

    return IAC



def optimizeIAC(PIA = 1.25, DIA = 4.0):

    """
    ============================================================================
    OPTIMIZEIAC
    ============================================================================
    """

    t = np.linspace(0, DIA, 500, endpoint = False)

    load = lambda x:(
           t[np.argmax(generateIAC(t = t, p = [x[0], x[1], x[2]]))] - PIA +
           10000 * abs(generateIAC(t = t, p = [x[0], x[1], x[2]])[DIA]) +
           abs(1.0 - integrateSimpson(f = generateIAC,
                                      p = [x[0], x[1], x[2]],
                                      a = 0,
                                      b = DIA,
                                      N = 500)))

    p = scipy.optimize.fmin(func = load, x0 = [15.0, 4.0, 3.0],
                            maxiter = 5000, maxfun = 5000)

    print "Optimized parameters:"
    print "a ~ " + str(round(p[0], 3))
    print "b ~ " + str(round(p[1], 3))
    print "c ~ " + str(round(p[2], 3))

    return p



def plotIAC(t, IAC, PIA, DIA):

    """
    ============================================================================
    PLOTIAC
    ============================================================================
    """

    # Initialize plot
    mpl.rc("font", size = 11)
    fig = plt.figure(0, figsize = (10, 8))
    sub = plt.subplot(111)

    # Define plot title
    plt.title("Insulin action curve for PIA = " + str(PIA) + " and DIA = " +
              str(DIA), weight = "semibold")

    # Define plot axis
    plt.xlabel("Time (h)", weight = "semibold")
    plt.ylabel("Insulin Action Curve (A.U.)", weight = "semibold")

    # Add potential to plot
    plt.plot(t, IAC, ls = "-", lw = 1.5, c = "grey")

    # Tighten up
    plt.tight_layout()

    # Show plot
    plt.show()



def main():

    """
    ============================================================================
    MAIN
    ============================================================================
    """

    N = 500
    PIA = 1.25
    DIA = 4.0

    t = np.linspace(0, DIA, 500, endpoint = False)
    parameters = optimizeIAC(PIA = PIA, DIA = DIA)
    IAC = generateIAC(t = t, p = parameters)
    plotIAC(t, IAC, PIA = PIA, DIA = DIA)



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
