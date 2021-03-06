#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    BG

    Author:   David Leclerc

    Version:  0.1

    Date:     30.06.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import numpy as np
import datetime



# USER LIBRARIES
import lib
import logger
import errors
import reporter
import base



# Define instances
Logger = logger.Logger("Profiles/BG.py")
Reporter = reporter.Reporter()



class PastBG(base.PastProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(PastBG, self).__init__()

        # Initialize number of valid recent BGs
        self.n = 0

        # Define type
        self.type = "Dot"

        # Define report info
        self.report = "BG.json"



    def load(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read units
        self.u = Reporter.get("pump.json", ["Units"], "BG")

        # Load rest
        super(PastBG, self).load()



    def count(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COUNT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define maximum age of BGs (m)
        T = 30

        # Read number of BGs
        N = len(self.T)

        # Initialize number of recent BGs
        n = 0

        # Check age of most recent BGs
        for i in range(N):

            # They should not be older than a certain duration
            if self.T[-(i + 1)] < self.end - datetime.timedelta(minutes = T):

                # Exit
                break

            # If so, update count
            else:

                # Update
                n += 1

        # Give user info
        Logger.debug("Found " + str(n) + " BGs within last " + str(T) + " m.")

        # Store number of valid recent BGs
        self.n = n



    def verify(self, n):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Verify there is enough recent BGs to do anything.
        """

        # Count recent BGs
        self.count()

        # Check for insufficient BG data
        if self.n < n:

            # Exit
            raise errors.MissingBGs()



    def impact(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            IMPACT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Check for insufficient data
        self.verify(2)

        # Get fit over last minutes
        [m, b] = np.polyfit(self.t[-self.n:], self.y[-self.n:], 1)

        # Return fit slope, which corresponds to BGI
        return m



class FutureBG(base.FutureProfile):

    def __init__(self, past):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(FutureBG, self).__init__()

        # Store past profile
        self.past = past

        # Define type
        self.type = "Dot"



    def build(self, IOB, ISF):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Use IOB and ISF to predict where BG will land after insulin activity
            is over, assuming a natural decay.
        """

        # Give user info
        Logger.debug("Decaying BG...")

        # Is there at least one recent BG?
        try:

            # Verify
            self.past.verify(1)

            # Link units
            self.u = self.past.u

        # It failed, so there isn't
        except:

            # Exit
            return

        # Reset previous BG predictions
        self.reset()

        # Define time references of profile
        self.time(IOB.start, IOB.end)

        # Get number of ISF steps
        n = len(IOB.T) - 1

        # Read latest BG
        BG = self.past.y[-1]

        # Give user info
        Logger.debug("Initial BG: " + str(BG) + " " + self.u + " " +
                     "(" + lib.formatTime(self.past.T[-1]) + ")")

        # Compute change in IOB (insulin that has kicked in within ISF step)
        for i in range(n):

            # Get step limits
            a = IOB.T[i]
            b = IOB.T[i + 1]

            # Give user info
            Logger.debug("Time: " + lib.formatTime(a) + " @ " +
                                    lib.formatTime(b))

            # Compute ISF
            isf = ISF.f(a)

            # Print ISF
            Logger.debug("ISF: " + str(isf) + " " + ISF.u)

            # Compute IOB change
            dIOB = IOB.y[i + 1] - IOB.y[i]

            # Give user info
            Logger.debug("dIOB: " + str(round(dIOB, 1)) + " " + IOB.u)

            # Compute BG change
            dBG = isf * dIOB

            # Give user info
            Logger.debug("dBG: " + str(round(dBG, 1)) + " " + self.u)

            # Add BG impact
            BG += dBG

            # Print eventual BG
            Logger.debug("BG: " + str(round(BG, 1)) + " " + self.u)

            # Store current BG
            self.T.append(b)
            self.y.append(BG)

        # Normalize
        self.normalize()

        # Derivate
        self.derivate()

        # Show
        self.show()



    def project(self, dt):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PROJECT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BG projection based on expected duration dt (h) of current BG trend
        """

        # Give user info
        Logger.info("Projection time: " + str(dt) + " h")

        # Read latest BG
        BG = self.past.y[-1]

        # Compute derivative to use when predicting future BG
        dBGdt = self.past.impact()

        # Predict future BG
        BG += dBGdt * dt

        # Return BG projection based on dBG/dt
        return BG



    def expect(self, dt, IOB):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            EXPECT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BG expectation after a certain time dt (h) based on IOB decay
        """

        # Give user info
        Logger.info("Expectation time: " + str(dt) + " h")

        # Get number of steps corresponding to expected BG
        n = dt / IOB.dt - 1

        # Check if expectation fits with previously computed BGs
        if int(n) != n or n < 0:

            # Exit
            raise errors.BadBGTime()

        # Return expected BG
        return self.y[int(n)]



    def analyze(self, IOB, ISF):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ANALYZE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Analyze and compute BG-related values.
        """

        # Give user info
        Logger.debug("Analyzing BG...")

        # Define prediction time (h)
        dt = 0.5

        # Compute projected BG based on latest CGM readings
        projectedBG = self.project(dt)

        # Compute BG variation due to IOB decay
        expectedBG = self.expect(dt, IOB)

        # Read BGI
        BGI = self.past.impact()

        # Compute BGI (dBG/dt) based on IOB decay
        expectedBGI = IOB.dydt[0] * ISF.y[0]

        # Compute deviation between BGs
        deltaBG = projectedBG - expectedBG

        # Compute deviation between BGIs
        deltaBGI = BGI - expectedBGI

        # Give user info (about BG)
        Logger.info("Expected BG: " + str(round(expectedBG, 1)) + " " +
                    self.u)
        Logger.info("Projected BG: " + str(round(projectedBG, 1)) + " " +
                    self.u)
        Logger.info("BG deviation: " + str(round(deltaBG, 1)) + " " +
                    self.u)

        # Give user info (about BGI)
        Logger.info("Expected BGI: " + str(round(expectedBGI, 1)) + " " +
                    self.u + "/h")
        Logger.info("BGI: " + str(round(BGI, 1)) + " " +
                    self.u + "/h")
        Logger.info("BGI deviation: " + str(round(deltaBGI, 1)) + " " +
                    self.u + "/h")

        # Give user info
        Logger.debug("End of BG analysis.")

        # Return computations
        return [deltaBG, BGI, expectedBGI]



    def dose(self, dBG, ISF, IDC):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DOSE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Compute bolus to bring back BG to target using ISF and IDC.
        """

        # Initialize conversion factor between dose and BG difference to target
        f = 0

        # Get number of ISF steps
        n = len(ISF.t) - 1

        # Compute factor
        for i in range(n):

            # Compute step limits
            a = ISF.t[i] - IDC.DIA
            b = ISF.t[i + 1] - IDC.DIA

            # Update factor with current step
            f += ISF.y[i] * (IDC.f(a) - IDC.f(b))

        # Compute bolus
        bolus = dBG / f

        # Return bolus
        return bolus



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Instanciate a BG profile
    BG = FutureBG(PastBG())

    # Load past
    BG.past.load()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()