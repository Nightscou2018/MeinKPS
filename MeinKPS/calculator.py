#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    calculator

    Author:   David Leclerc

    Version:  0.1

    Date:     27.05.2016

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import datetime
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt



# USER LIBRARIES
import lib
import logger
import reporter
from Profiles import *



# Define instances
Logger = logger.Logger("calculator.py")
Reporter = reporter.Reporter()



# CONSTANTS
BG_HYPO_LIMIT = 4.2



class Calculator(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize current time
        self.now = None

        # Initialize DIA
        self.DIA = None

        # Initialize IDC
        self.IDC = None

        # Give calculator a basal profile
        self.basal = basal.Basal()

        # Give calculator a TB profile
        self.TB = TB.TB()

        # Give calculator a bolus profile
        self.bolus = bolus.Bolus()

        # Give calculator a suspend profile
        self.suspend = suspend.Suspend()

        # Give calculator a resume profile
        self.resume = resume.Resume()

        # Initialize net insulin profile
        self.net = net.Net()

        # Give calculator an IOB profile
        self.IOB = IOB.FutureIOB(IOB.PastIOB())

        # Give calculator a COB profile
        self.COB = COB.COB()

        # Give calculator an ISF profile
        self.ISF = ISF.ISF()

        # Give calculator a CSF profile
        self.CSF = CSF.CSF()

        # Give calculator a BG targets profile
        self.BGTargets = BGTargets.BGTargets()

        # Give calculator a BG profile
        self.BG = BG.FutureBG(BG.PastBG())

        # Initialize pump's max values
        self.max = {"Basal": None,
                    "Bolus": None}



    def run(self, now):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RUN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define current time
        self.now = now

        # Load components
        self.load()

        # Prepare components
        self.prepare()

        # Run autosens
        #self.autosens()

        # Recommend and return TB
        return self.recommend()



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read DIA
        self.DIA = Reporter.get("pump.json", ["Settings"], "DIA")

        # Give user info
        Logger.info("DIA: " + str(self.DIA) + " h")

        # Read max basal
        self.max["Basal"] = Reporter.get("pump.json", ["Settings"], "Max Basal")

        # Give user info
        Logger.info("Max basal: " + str(self.max["Basal"]) + " U/h")

        # Read max bolus
        self.max["Bolus"] = Reporter.get("pump.json", ["Settings"], "Max Bolus")

        # Give user info
        Logger.info("Max bolus: " + str(self.max["Bolus"]) + " U")



    def prepare(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PREPARE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Compute past start of insulin action
        past = self.now - datetime.timedelta(hours = self.DIA)

        # Compute future end of insulin action
        future = self.now + datetime.timedelta(hours = self.DIA)

        # Build net insulin profile
        self.net.build(past, self.now, self.basal, self.TB, self.suspend,
                                       self.resume, self.bolus)

        # Define IDC
        self.IDC = IDC.WalshIDC(self.DIA)
        #self.IDC = IDC.FiaspIDC(self.DIA)

        # Build past IOB profile
        self.IOB.past.build(past, self.now)

        # Build future IOB profile
        self.IOB.build(self.net, self.IDC)

        # Build COB profile
        #self.COB.build(past, self.now)

        # Build future ISF profile
        self.ISF.build(self.now, future)

        # Build future CSF profile
        self.CSF.build(self.now, future)

        # Build future BG targets profile
        self.BGTargets.build(self.now, future)

        # Build past BG profile
        self.BG.past.build(past, self.now)

        # Build future BG profile
        self.BG.build(self.IOB, self.ISF)



    def computeDose(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COMPUTEDOSE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Compute the necessary insulin amount at the current time  based on
        latest BG input and future target, taking into account ISF step curve
        over the next DIA hours (assuming natural decay of insulin).
        """

        # Give user info
        Logger.debug("Computing insulin dose...")

        # Check for insufficient data
        self.BG.past.verify(1)

        # Get current data
        BG = self.BG.past.y[-1]
        ISF = self.ISF.y[0]
        IOB = self.IOB.y[0]

        # Compute target by the end of insulin action
        targetRangeBG = self.BGTargets.y[-1]
        targetBG = np.mean(targetRangeBG)

        # Compute eventual BG after complete IOB decay
        naiveBG = self.BG.expect(self.DIA, self.IOB)

        # Compute BG deviation based on CGM readings and expected BG due to IOB
        # decay
        [deltaBG, BGI, expectedBGI] = self.BG.analyze(self.IOB, self.ISF)

        # Update eventual BG
        eventualBG = naiveBG + deltaBG

        # Compute BG difference with average target
        dBG = targetBG - eventualBG

        # Compute required dose
        dose = self.BG.dose(dBG, self.ISF, self.IDC)

        # Give user info
        Logger.info("BG target: " + str(targetBG) + " " + self.BG.u)
        Logger.info("Current BG: " + str(BG) + " " + self.BG.u)
        Logger.info("Current ISF: " + str(ISF) + " " + self.ISF.u)
        Logger.info("Current IOB: " + str(IOB) + " " + self.IOB.u)
        Logger.info("Naive eventual BG: " + str(naiveBG) + " " + self.BG.u)
        Logger.info("Eventual BG: " + str(eventualBG) + " " + self.BG.u)
        Logger.info("dBG: " + str(dBG) + " " + self.BG.u)
        Logger.info("Recommended dose: " + str(dose) + " " + "U")

        # Look for conflictual info
        if (np.sign(BGI) == -1 and eventualBG > max(targetRangeBG) or
            np.sign(BGI) == 1 and eventualBG < min(targetRangeBG)):

            # Give user info
            Logger.warning("Conflictual information: BG decreasing/rising " +
                           "although expected to land higher/lower than " +
                           "target range.")

        # Return dose
        return dose



    def computeTB(self, dose):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COMPUTETB
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Compute TB to enact given a recommended insulin dose.
        """

        # Give user info
        Logger.debug("Computing TB to enact...")

        # Get current data
        basal = self.basal.y[-1]

        # Define time to enact equivalent of dose (h)
        T = 0.5

        # When too close to hypo
        if self.BG.past.y[-1] < BG_HYPO_LIMIT:

            # Stop insulin delivery
            dB = -basal

        # Otherwise
        else:

            # Find required basal difference to enact over given time (round to
            # pump's precision)
            dB = dose / T

        # Compute TB to enact 
        TB = basal + dB

        # Give user info
        Logger.info("Current basal: " + str(basal) + " U/h")
        Logger.info("Required basal difference: " + str(dB) + " U/h")
        Logger.info("Temporary basal to enact: " + str(TB) + " U/h")
        Logger.info("Enactment time: " + str(T) + " h")

        # Convert enactment time to minutes
        T *= 60

        # Return TB recommendation
        return [TB, "U/h", T]



    def limitTB(self, TB):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LIMITTB
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Limit too low/high TBs.
        """

        # Destructure TB
        [rate, units, duration] = TB

        # Negative TB rate
        if rate < 0:

            # Give user info
            Logger.warning("External action required: negative basal " +
                           "required. Eat something!")

            # Stop insulin delivery
            rate = 0

        # Positive TB
        elif rate > 0:

            # Get basal info
            basal = self.basal.y[-1]
            maxDailyBasal = self.basal.max
            maxBasal = self.max["Basal"]

            # Define max basal rate allowed (U/h)
            maxRate = min(4 * basal, 3 * maxDailyBasal, maxBasal)

            # Give user info
            Logger.info("Theoretical max basal: " + str(maxBasal) + " U/h")
            Logger.info("4x current basal: " + str(4 * basal) + " U/h")
            Logger.info("3x max daily basal: " + str(3 * maxDailyBasal) + " " +
                        "U/h")

            # TB exceeds max
            if rate > maxRate:

                # Give user info
                Logger.warning("External action required: maximal basal " +
                               "exceeded. Enact dose manually!")

                # Max it out
                rate = maxRate

        # No TB
        else:

            # Give user info
            Logger.info("No modification to insulin dosage necessary.")

        # Return limited TB
        return [rate, units, duration]



    def snooze(self, TB):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SNOOZE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Snooze enactment of high TBs for a while after eating.
        """

        # Get last carbs
        lastCarbs = Reporter.getRecent(self.now, "treatments.json",
                                                 ["Carbs"], 1)

        # Destructure TB
        [rate, units, duration] = TB

        # Define snooze duration (h)
        snooze = 0.5 * self.DIA

        # Snooze criteria (no high temping after eating)
        if lastCarbs:

            # Get last meal time and format it to datetime object
            lastTime = lib.formatTime(max(lastCarbs))

            # Compute elapsed time since (h)
            d = (self.now - lastTime).total_seconds() / 3600.0

            # If snooze necessary
            if d < snooze:

                # Compute remaining time (m)
                T = int(round((snooze - d) * 60))

                # Give user info
                Logger.warning("Bolus snooze (" + str(snooze) + " h). If no " +
                               "more bolus issued, looping will restart in " +
                               str(T) + " m.")

                # Snooze
                return True

        # Do not snooze
        return False



    def recommend(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RECOMMEND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Recommend a bolus based on latest BG and future target average, taking
        into account ISF step curve over the next DIA hours (assuming natural
        decay of insulin).
        """

        # Give user info
        Logger.debug("Recommending treatment...")

        # Compute recommended dose
        dose = self.computeDose()

        # Compute corresponding TB
        TB = self.computeTB(dose)

        # Limit it
        TB = self.limitTB(TB)

        # Snoozing of TB enactment required?
        if self.snooze(TB):

            # No TB recommendation
            TB = None

        # If recommendation was not canceled
        if TB is not None:

            # Destructure TB
            [rate, units, duration] = TB

            # Give user info
            Logger.info("Recommended TB: " + str(rate) + " " + units + " (" +
                                             str(duration) + " m)")

        # Return recommendation
        return TB



    def autosens(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            AUTOSENS
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get last 24 hours of BGs
        BGs = Reporter.getRecent(self.now, "BG.json", [], 7, True)

        # Show them
        lib.JSONize(BGs)

        # Build BG profile for last 24 hours
        BGProfile = 0



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize plot
        mpl.rc("font", size = 10, family = "Ubuntu")
        fig = plt.figure(0, figsize = (10, 8))
        axes = [plt.subplot(221),
                plt.subplot(222),
                plt.subplot(223),
                plt.subplot(224)]

        # Define titles
        titles = ["BG", "Net Insulin Profile", "IOB", "COB"]

        # Define axis labels
        x = ["(h)"] * 4
        y = ["(" + self.BG.u + ")", "(U/h)", "(U)", "(g)"]

        # Define axis limits
        xlim = [[-self.DIA, self.DIA]] * 4
        ylim = [[2, 20], None, None, None]

        # Define subplots
        for i in range(4):

            # Set titles
            axes[i].set_title(titles[i], fontweight = "semibold")

            # Set x-axis labels
            axes[i].set_xlabel(x[i])

            # Set y-axis labels
            axes[i].set_ylabel(y[i])

            # Set x-axis limits
            axes[i].set_xlim(xlim[i])

        # Set y-axis limits
        axes[0].set_ylim(ylim[0])

        # Add BGs to plot
        axes[0].plot(self.BG.past.t, self.BG.past.y,
                     marker = "o", ms = 3.5, lw = 0, c = "red")

        # Add BG predictions to plot
        axes[0].plot(self.BG.t, self.BG.y,
                     marker = "o", ms = 3.5, lw = 0, c = "black")

        # Add net insulin profile to plot
        axes[1].step(self.net.t, np.append(0, self.net.y[:-1]),
                     lw = 2, ls = "-", c = "purple")

        # Add past IOB to plot
        axes[2].plot(self.IOB.past.t, self.IOB.past.y,
                     marker = "o", ms = 3.5, lw = 0, c = "orange")

        # Add IOB predictions to plot
        axes[2].plot(self.IOB.t, self.IOB.y,
                     lw = 2, ls = "-", c = "black")

        # Add COB to plot
        axes[3].plot([-self.DIA, 0], [0, 0],
                     lw = 2, ls = "-", c = "#99e500")

        # Add COB predictions to plot
        axes[3].plot([0, self.DIA], [0, 0],
                     lw = 2, ls = "-", c = "black")

        # Tighten up
        plt.tight_layout()

        # Show plot
        plt.show()



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Get current time
    now = datetime.datetime.now() - datetime.timedelta(days = 0)

    # Instanciate a calculator
    calculator = Calculator()

    # Run calculator
    calculator.run(now)

    # Run autosens
    #calculator.autosens()

    # Show components
    calculator.show()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()