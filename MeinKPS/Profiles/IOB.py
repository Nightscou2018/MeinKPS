#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    IOB

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
import copy



# USER LIBRARIES
import lib
import logger
import reporter
import base



# Define instances
Logger = logger.Logger("Profiles/IOB.py")
Reporter = reporter.Reporter()



class PastIOB(base.PastProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(PastIOB, self).__init__()

        # Define units
        self.u = "U"

        # Define type
        self.type = "Dot"

        # Define report info
        self.report = "treatments.json"
        self.branch = ["IOB"]



class FutureIOB(base.FutureProfile):

    def __init__(self, past):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(FutureIOB, self).__init__()

        # Store past profile
        self.past = past

        # Define timestep (h)
        self.dt = 5.0 / 60.0

        # Define units
        self.u = "U"

        # Define type
        self.type = "Dot"

        # Define report info
        self.report = "treatments.json"
        self.branch = ["IOB"]



    def build(self, net, IDC):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            BUILD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        Logger.debug("Predicting IOB...")

        # Reset previous IOB predictions
        self.reset()

        # Define time references of profile
        self.time(net.end, net.end + datetime.timedelta(hours = IDC.DIA))

        # Compute number of steps
        n = int(IDC.DIA / self.dt) + 1

        # Generate time axis
        t = np.linspace(0, IDC.DIA, n)

        # Convert to datetime objects
        t = [datetime.timedelta(hours = x) for x in t]

        # Compute IOB decay
        for i in range(n):

            # Compute prediction time
            T = net.end + t[i]

            # Copy net insulin profile
            new = copy.copy(net)

            # Reset it
            new.reset()

            # Initialize start/end times
            new.T.append(new.start)
            new.T.append(new.end)

            # Initialize start/end values
            new.y.append(None)
            new.y.append(0)

            # Fill profile
            new.fill(net)

            # Smooth profile
            new.smooth()

            # Normalize profile
            new.normalize(T)

            # Compute IOB for current time
            IOB = self.compute(new, IDC)

            # Store prediction time
            self.T.append(T)

            # Store IOB
            self.y.append(IOB)

        # Normalize
        self.normalize()

        # Derivate
        self.derivate()

        # Store current IOB
        self.store()

        # Show
        self.show()



    def compute(self, net, IDC):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            COMPUTE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Decouple net insulin profile components
        t = net.t
        y = net.y

        # Initialize IOB
        IOB = 0

        # Get number of steps
        n = len(t) - 1

        # Compute IOB
        for i in range(n):

            # Compute remaining IOB factor based on integral of IDC
            r = IDC.F(t[i + 1]) - IDC.F(t[i])

            # Compute active insulin remaining for current step
            IOB += r * y[i]

        # Give user info
        Logger.debug("IOB: " + str(IOB) + " U")

        # Return IOB
        return IOB



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            Note: only stores current IOB for later displaying purposes.
        """

        # Give user info
        Logger.debug("Adding current IOB to report: '" + self.report + "'...")

        # Add entry
        Reporter.add(self.report, self.branch, {self.T[0]: round(self.y[0], 3)})