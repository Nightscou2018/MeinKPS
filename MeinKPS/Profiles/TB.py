#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    TB

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
import datetime



# USER LIBRARIES
import errors
import base



class TB(base.PastProfile):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start initialization
        super(TB, self).__init__()

        # Renitialize units
        self.u = []

        # Define report info
        self.report = "treatments.json"
        self.branch = ["Temporary Basals"]



    def decouple(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECOUPLE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Start decoupling
        super(TB, self).decouple()

        # Get number of steps
        n = len(self.T)

        # Decouple components
        for i in range(n):

            # Get duration
            self.d.append(datetime.timedelta(minutes = self.y[i][2]))

            # Get units
            self.u.append(self.y[i][1])

            # Get rate
            self.y[i] = self.y[i][0]

        # Verify units
        self.verifyUnits()



    def verifyUnits(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFYUNITS
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get number of steps
        n = len(self.T)

        # Check for use of incorrect units within profile
        for i in range(n):

            # Units currently supported
            if self.u[i] != "U/h":

                # Give user info
                raise errors.BadTBUnits()