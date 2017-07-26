#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    reporter

    Author:   David Leclerc

    Version:  0.1

    Date:     30.05.2016

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: ...

    Notes:    ...

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# LIBRARIES
import json
import datetime
import os
import sys



# USER LIBRARIES
import lib
import errors



class Reporter:

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define source path
        self.src = os.getcwd() + "/" + "Reports/"
        #self.src = "/home/pi/MeinKPS/MeinKPS/Reports/"

        # Define export path
        self.out = self.src + "Recent/"
        #self.out = "/home/pi/MeinKPS/MeinKPS/Reports/Recent/"

        # Initialize reports
        self.reports = []



    def new(self, name = None, path = None, date = None, json = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            NEW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Loop on reports
        for report in self.reports:

            # Check if report already exists
            if report.name == name and report.date == date:

                # Give user info
                print ("Report '" + name + "' (" + str(date) + ") already " +
                       "loaded.")

                # Skip
                return False

        # Generate new report
        self.reports.append(Report(name, path, date, json))

        # Success
        return True



    def reset(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Reset reports
        self.reports = []



    def load(self, name, dates = None, path = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            LOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize number of reports to load
        n = 0

        # No path
        if path is None:

            # Define source
            path = self.src

        # No dates
        if dates is None:

            # Define path
            p = path

            # Generate new report
            if self.new(name, p):

                # Update count
                n += 1

        # Otherwise
        else:

            # Make sure dates are given in list form
            if type(dates) is not list:

                # Convert type
                dates = [dates]

            # Format dates
            dates = [datetime.datetime.strftime(d, "%Y/%m/%d") for d in dates]

            # Make sure dates are sorted out and only appear once
            # This can deal with both list and dict types
            dates = lib.uniqify(dates)

            # Loop on dates
            for d in dates:

                # Define path
                p = path + d + "/"

                # Generate new report
                if self.new(name, p, d):

                    # Update count
                    n += 1

        # Load report(s)
        for i in range(n):

            # Get current new report
            report = self.reports[-(i + 1)]

            # Give user info
            print ("Loading report: '" + report.name + "' (" +
                   str(report.date) + ")")

            # Make sure report exists
            Path(report.path).find(name)

            # Open report
            with open(report.path + name, "r") as f:

                # Load JSON
                report.json = json.load(f)



    def unload(self, name, date = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            UNLOAD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # If date
        if date is not None:

            # Get current date
            d = datetime.datetime.strftime(date, "%Y/%m/%d")

        # Loop on reports
        for i in range(len(self.reports)):

            # Get current report
            report = self.reports[i]

            # If name fits
            if report.name != name:

                # Skip
                continue

            # If dates
            if date is not None and report.date != d:

                # Skip
                continue

            # Give user info
            print ("Unloading report: " + report.name + " (" +
                   str(report.date) + ")")

            # Delete it
            del self.reports[i]

            # Exit
            return

        # Report not found
        sys.exit("Report could not be found, thus not unloaded.")



    def save(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SAVE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Rewrite reports
        for report in self.reports:

            # If report was modified
            if report.modified:

                # Give user info
                print ("Updating report: '" + report.name + "' (" +
                       str(report.date) + ")")

                # Rewrite report
                with open(report.path + report.name, "w") as f:

                    # Dump JSON
                    json.dump(report.json, f,
                              indent = 4,
                              separators = (",", ": "),
                              sort_keys = True)

                # Report was updated
                report.modified = False



    def export(self, name):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            EXPORT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Touch export file
        Path(self.out).find(name)

        # Get recent data
        data = self.getLatest(name, [])

        # Store recent data
        with open(self.out + name, "w") as f:

            # Dump JSON
            json.dump(data, f,
                      indent = 4,
                      separators = (",", ": "),
                      sort_keys = True)



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Loop on reports
        for report in self.reports:

            # Show report
            report.show()



    def showBranch(self, branch):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOWBRANCH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Format path
        return " > ".join(["."] + branch)



    def getReport(self, name, date = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETREPORT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # If date
        if date is not None:

            # Get and format date
            date = datetime.datetime.strftime(date, "%Y/%m/%d")

        # Give user info
        print "Getting report: '" + name + "' (" + str(date) + ")"

        # Loop through reports
        for report in self.reports:

            # Check if names match
            if report.name != name:

                # Skip
                continue

            # Check if dates match
            if report.date != date:

                # Skip
                continue

            # Return report
            return report

        # Give user info
        sys.exit("Did not find report.")



    def getSection(self, report, branch, make = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETSECTION
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Make sure section branch is of list type
        if type(branch) is not list:

            # Raise error
            raise errors.BadPath

        # Read section depth: if it is equal to 0, the following loop is
        # skipped and the section corresponds to the whole report
        d = len(branch)

        # First level section is whole report
        section = report.json

        # Give user info
        print "Getting section: " + self.showBranch(branch)

        # Loop through whole report to find section
        for i in range(d):

            # Get current branch
            b = branch[i]

            # Check if section report exists
            if b not in section:

                # Make section if desired
                if make:
                
                    # Give user info
                    print "Section not found. Making it..."

                    # Create it
                    section[b] = {}

                # Otherwise
                else:

                    # Raise error
                    raise errors.NoSection

            # Update section
            section = section[b]

        # Return section
        return section



    def getEntry(self, section, key):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETENTRY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Getting entry: " + str(key)

        # Look if entry exists
        if key in section:

            # Get corresponding value
            value = section[key]

            # Give user info
            print "Entry found."

            # Return entry for external access
            return value

        # Otherwise
        else:

            # Give user info
            print "No matching entry found."

            # Return nothing
            return None



    def deleteEntry(self, section, key):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DELETEENTRY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Deleting entry: " + str(key)

        # If it does, delete it
        if key in section:

            # Delete entry
            del section[key]

            # Give user info
            print "Entry deleted."

        else:

            # Give user info
            print "No such entry."



    def addEntry(self, section, entry, overwrite = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ADDENTRY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Adding entry:"

        # Show entry
        lib.printJSON(entry)

        # Decouple entry
        (key, value) = entry.items()[0]

        # Look if entry is already in report
        if key in section and not overwrite:

            # Give user info
            print "Entry already exists."

        # If not, write it down
        else:

            # Add entry to report
            section[key] = value

            # If overwritten
            if overwrite:

                # Give user info
                print "Entry overwritten."

            # Otherwise
            else:

                # Give user info
                print "Entry added."



    def add(self, name, branch, entries, overwrite = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            ADD
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # If entries are dated
        if type(min(entries)) is datetime.datetime:

            # Initialize date
            date = True

            # Load report(s)
            self.load(name, entries.keys())

        # Otherwise
        else:

            # Initialize date
            date = None

            # Load report
            self.load(name)

            # Get it
            report = self.getReport(name)

            # Get section
            section = self.getSection(report, branch, True)

        # Loop through entries
        for key in sorted(entries):

            # Get value
            value = entries[key]

            # If date
            if date is not None:

                # Get date
                d = key.date()

                # Format key
                key = lib.formatTime(key)

                # If date is different than previous one
                if d != date:

                    # Update date
                    date = d

                    # Get report
                    report = self.getReport(name, date)

                    # Get section
                    section = self.getSection(report, branch, True)

            # Add entry
            self.addEntry(section, {key: value}, overwrite)

            # Report was modified
            report.modified = True

        # Save reports
        self.save()



    def get(self, name, branch, key = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # If key is dated
        if type(key) is datetime.datetime:

            # Load report
            self.load(name, key)

            # Get date
            date = key.date()

            # Format key
            key = lib.formatTime(key)

            # Get report
            report = self.getReport(name, date)

        # Otherwise
        else:

            # Load report
            self.load(name)

            # Get it
            report = self.getReport(name)

        # Get section
        section = self.getSection(report, branch)

        # If key was provided
        if key is not None:

            # Return corresponding value
            return self.getEntry(section, key)

        # Otherwise
        else:

            # Return section
            return section



    def getLatest(self, name, branch, n = 2):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            GETLATEST
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Scan for all possible report paths
        paths = Path(self.src).scan(name)

        # If no possible reports found
        if not paths:

            # Exit
            sys.exit("Nothing found for '" + name + "'.")

        # Initialize dates
        dates = []

        # Loop on paths
        for p in paths:

            # Get date from path
            dates.append(Path(p).date())

        # Initialize dict for merged entries
        entries = {}

        # Initialize number of reports merged
        N = 0

        # Loop on dates, starting with the latest one
        for d in sorted(dates, reverse = True):

            # Check if enough recent reports were fetched
            if N == n:

                # Quit
                break

            # Load report
            self.load(name, d)

            # Get report
            report = self.getReport(name, d)

            # Try getting section
            try:

                # Get section
                section = self.getSection(report, branch)

            # In case of failure
            except Exception as e:

                # Show error message
                print e.message

                # Unload report
                self.unload(name, d)

                # Skip
                continue

            # Give user info
            print "Merging '" + report.name + "' (" + report.date + ")"

            # Merge entries
            entries = lib.mergeDict(entries, section)

            # Update number of reports merged
            N += 1

        # Give user info
        print "Merged entries for " + str(N) + " most recent report(s):"

        # Show entries
        lib.printJSON(entries)

        # Return entries
        return entries



    def increment(self, name, branch, key, date = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INCREMENT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load report
        self.load(name, date)

        # Get report
        report = self.getReport(name, date)

        # Get section
        section = self.getSection(report, branch)

        # Increment entry
        self.addEntry(section, {key: self.getEntry(section, key) + 1}, True)

        # Report was modified
        report.modified = True

        # Save report
        self.save()



class Report:

    def __init__(self, name = None, path = None, date = None, json = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize report attributes
        self.name = name
        self.path = path
        self.date = date
        self.json = json
        self.modified = False



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Show report
        lib.printJSON({"Name": self.name,
                       "Path": self.path,
                       "Date": self.date,
                       "JSON": self.json,
                       "Modified": self.modified})



class Path:

    def __init__(self, path):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # If input is string
        if type(path) is str:

            # Store it
            self.str = path

            # Generate a list from it
            self.list = self.split()

        # If it is list
        elif type(path) is list:

            # Store it
            self.list = path

            # Generate a string from it
            self.str = self.merge()

        # Compute path depth
        self.depth = len(self.list)



    def split(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SPLIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Split path
        return [p for p in self.str.replace("\\", "/")
                                   .replace("//", "/")
                                   .split("/") if p != ""]



    def merge(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            MERGE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Note: The first "/" will only work for Linux
        """

        # Merge path
        return "/" + "/".join(self.list) + "/"
        #return "/".join(self.list) + "/"



    def date(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DATE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize date
        date = []

        # Initialize path
        path = self.str

        # Loop 3 directories up to get corresponding date
        for i in range(3):

            # Split path
            path, file = os.path.split(path)

            # Add date component
            date.append(int(file))

        # Reverse date
        date.reverse()

        # Return datetime object
        return datetime.datetime(*date)



    def find(self, file = None, n = 1):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            FIND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Stringify current path
        path = Path(self.list[:n]).str

        # Look for path
        if n <= self.depth:

            # If it does not exist
            if not os.path.exists(path):

                # Give user info
                print "Making '" + path + "/'..."

                # Make it
                os.makedirs(path)

            # Contine looking
            self.find(file, n + 1)

        # Look for file
        elif file is not None:

            # Complete path with filename
            path += file

            # If it does not exist
            if not os.path.exists(path):

                # Give user info
                print "Making '" + path + "'..."

                # Create it
                with open(path, "w") as f:

                    # Dump empty dict
                    json.dump({}, f)



    def scan(self, file, path = None, results = None, n = 1):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SCAN
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # On first run
        if n == 1:

            # Initialize results
            results = []

            # Read source path
            path = self.str

            # Give user info
            print ("Scanning for '" + str(file) + "' within '" + str(path) +
                   "'...")

        # Get all files from path
        files = os.listdir(path)

        # Get inside path
        os.chdir(path)

        # Upload files
        for f in files:

            # If file
            if os.path.isfile(f):

                # Check if filename fits
                if f == file:

                    # Store path
                    results.append(os.getcwd())

            # If directory and a digit (because a date)
            elif os.path.isdir(f) and f.isdigit():

                # Scan further
                self.scan(file, f, results, n + 1)

        # Go back up
        os.chdir("..")

        # If first level
        if n == 1:

            # Return results
            return results



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Instanciate a reporter for me
    reporter = Reporter()

    # Load reports
    #reporter.load("pump.json")

    # Get basal profile from pump report
    #reporter.get("pump.json", [], "Basal Profile (Standard)")

    # Unload pump report
    #reporter.unload("pump.json")

    # Add entries to test report
    #reporter.add("test.json", ["A", "B"], {"C": 0, "D": 1})

    # Get most recent BG
    #reporter.getLatest("BG.json", [], 3)
    #reporter.getLatest("treatments.json", ["Temporary Basals"])

    # Export latest data
    #reporter.export("BG.json")
    #reporter.export("treatments.json")

    # Get latest pump power time
    reporter.getLatest("history.json", ["Pump"], "Power")



# Run this when script is called from terminal
if __name__ == "__main__":
    main()