#! /usr/bin/python

"""
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Title:    pump

    Author:   David Leclerc

    Version:  0.3

    Date:     20.02.2017

    License:  GNU General Public License, Version 3
              (http://www.gnu.org/licenses/gpl.html)

    Overview: This is a script that contains a handful of commands that can be
              sent wirelessly to a Medtronic RF Paradigm pump through a Carelink
              USB stick. Please use carefully!

    Notes:    - When the battery is low, the stick will not be able to
                communicate with the pump anymore.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

# TODO: - Make sure the maximal TBR and bolus are correctly
#         set, that is higher than or equal to the TBR and/or bolus that will be
#         issued.
#       - Test with alarm set on pump
#       - Test with pump reservoir empty or almost empty
#       - Deal with timezones, DST, year switch
#       - Run series of tests overnight
#       X Make sure enacted bolus are detected!
#       - No point in reissuing same TBR?
#       - Decode square/dual boluses?
#       - Add "change battery" suggestion when no more response received from
#         stick
#       - Reduce session time if looping every 5 minutes?
#       - Deal with manually set TBR. Read end of TBR?
#       - What if session of commands is longer than pump's remaining RF
#         communication time? Detect long session time and compare it with 
#         remaining one? 



# LIBRARIES
import datetime
import json
import time



# USER LIBRARIES
import lib
import commands
import stick
import records
import reporter
import errors



# Define a reporter
Reporter = reporter.Reporter()



class Pump(object):

    # PUMP CHARACTERISTICS
    serial         = 503593 # 799163
    executionDelay = 1 # 5  # Time (s) needed for pump command execution



    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give the pump a stick
        self.stick = stick.Stick()

        # Link the pump to the stick's handle
        self.handle = self.stick.handle

        # Give the pump a power instance
        self.power = Power(self)

        # Give the pump a time instance
        self.time = Time(self)

        # Give the pump a model instance
        self.model = Model(self)

        # Give the pump a firmware instance
        self.firmware = Firmware(self)

        # Give the pump an instance for its buttons
        self.buttons = Buttons(self)

        # Give the pump a battery instance
        self.battery = Battery(self)

        # Give the pump a reservoir instance
        self.reservoir = Reservoir(self)

        # Give the pump a status instance
        self.status = Status(self)

        # Give the pump a settings instance
        self.settings = Settings(self)

        # Give the pump units
        self.units = {"BG": BGU(self),
                      "C": CU(self),
                      "TBR": TBRU(self)}

        # Give the pump a BG targets instance
        self.BGTargets = BGTargets(self)

        # Give the pump an ISF instance
        self.ISF = ISF(self)

        # Give the pump a CSF instance
        self.CSF = CSF(self)

        # Give the pump a daily totals instance
        self.dailyTotals = DailyTotals(self)

        # Give the pump a history instance
        self.history = History(self)

        # Give the pump a bolus instance
        self.bolus = Bolus(self)

        # Give the pump a TBR instance
        self.TBR = TBR(self)



    def start(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            START
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Starting dialogue with pump..."

        # Start stick
        self.stick.start()

        # Power pump's radio transmitter if necessary
        self.power.verify()



    def stop(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STOP
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Stopping dialogue with the pump..."

        # Stop stick
        self.stick.stop()



class Power(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define time needed for the pump's radio to power up (s)
        self.powerTime = 10

        # Define time for which pump will listen to RFs (m)
        self.sessionTime = 10

        # Link with its respective command
        self.command = commands.PowerPump(pump, self)



    def verify(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Load pump's report
        Reporter.load("pump.json")

        # Get current time
        now = datetime.datetime.now()

        # Read last time pump's radio transmitter was power up
        then = Reporter.getEntry([], "Power")

        # Format time
        then = lib.formatTime(then)

        # Compute time since last power up
        delta = now - then

        # Generate a datetime object for the pump's RF sessions' length
        session = datetime.timedelta(minutes = self.sessionTime)

        # Power up pump if necessary
        if delta > session:

            # Give user info
            print "Pump's radio transmitter will be turned on..."

            # Power up pump's RF transmitter
            self.do()

        else:

            # Give user info
            print ("Pump's radio transmitter is already on. Remaining time: " +
                   str(self.sessionTime - delta.seconds / 60) + " m")



    def do(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DO
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare command
        self.command.prepare()

        # Do command
        self.command.do(False)

        # Get current time
        now = datetime.datetime.now()

        # Format time
        now = lib.formatTime(now)

        # Store power up time
        Reporter.storePowerTime(now)



class Time(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize value
        self.value = None

        # Link with its respective command
        self.command = commands.ReadPumpTime(pump, self)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare command
        self.command.prepare()

        # Do command
        self.command.do()

        # Give user info
        print "Pump time: " + self.value



class Model(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize value
        self.value = None

        # Link with its respective command
        self.command = commands.ReadPumpModel(pump, self)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare command
        self.command.prepare()

        # Do command
        self.command.do()

        # Store pump model
        Reporter.storeModel(self.value)

        # Give user info
        print "Pump model: " + str(self.value)



class Firmware(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize value
        self.value = None

        # Link with its respective command
        self.command = commands.ReadPumpFirmware(pump, self)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare command
        self.command.prepare()

        # Do command
        self.command.do()

        # Store pump model
        Reporter.storeFirmware(self.value)

        # Give user info
        print "Pump firmware: " + str(self.value)



class Buttons(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Buttons
        self.values = {"EASY": 0, "ESC": 1, "ACT": 2, "UP": 3, "DOWN": 4}

        # Link with its respective command
        self.command = commands.PushPumpButton(pump, self)



    def push(self, button):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            PUSH
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare command
        self.command.prepare(button)

        # Do command
        self.command.do(False)

        # Give user info
        print "Pushed button: " + button



class Battery(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Note: The battery seems to stop communicating after some values of 1.2 V
              have been read. Set a warning at this point?
        """

        # Initialize value
        self.value = None

        # Link with its respective command
        self.command = commands.ReadPumpBattery(pump, self)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Define request infos
        info = "Reading battery level..."

        # Prepare command
        self.command.prepare()

        # Do command
        self.command.do()

        # Get current time
        now = datetime.datetime.now()

        # Format time
        now = lib.formatTime(now)

        # Add current battery level to pump report
        Reporter.addBatteryLevel(now, self.value)

        # Give user info
        print "Pump's battery level: " + str(self.value) + " V"



class Reservoir(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize value
        self.value = None

        # Link with its respective command
        self.command = commands.ReadPumpReservoir(pump, self)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare command
        self.command.prepare()

        # Do command
        self.command.do()

        # Get current time
        now = datetime.datetime.now()

        # Format time
        now = lib.formatTime(now)

        # Add current reservoir level to pump report
        Reporter.addReservoirLevel(now, self.value)

        # Give user info
        print "Remaining amount of insulin: " + str(self.value) + " U"



class Status(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize value
        self.values = {"Normal": None,
                       "Bolusing": None,
                       "Suspended": None}

        # Link with its respective commands
        self.commands = {"Read": commands.ReadPumpStatus(pump, self),
                         "Suspend": commands.SuspendPump(pump, self),
                         "Resume": commands.ResumePump(pump, self)}



    def verify(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Overview: Verify pump's status before enabling any desired course of
                  action (e.g. bolusing or enacting a TBR).
        """

        # Read pump status
        self.read()

        # Check if pump is ready to take action
        if not self.values["Normal"]:

            # Give user info
            print "There seems to be a problem with the pump. Try again later."

            return False

        elif self.values["Bolusing"]:

            # Give user info
            print "Pump is bolusing. Try again later."

            return False

        elif self.values["Suspended"]:

            # Give user info
            print "Pump is suspended, but will be asked to resume activity."

            # Resume pump activity
            self.resume()

        # Give user info
        print "Pump's status allows desired course of action. Proceeding..."

        return True



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare command
        self.commands["Read"].prepare()

        # Do command
        self.commands["Read"].do()

        # Give user info
        print "Pump's status: " + str(self.values)



    def suspend(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SUSPEND
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare command
        self.commands["Suspend"].prepare()

        # Do command
        self.commands["Suspend"].do(False)



    def resume(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            RESUME
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare command
        self.commands["Resume"].prepare()

        # Do command
        self.commands["Resume"].do(False)



class Settings(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize values
        self.values = {"IAC": None,
                       "Max Bolus": None,
                       "Max Basal": None}

        # Link with its respective command
        self.command = commands.ReadPumpSettings(pump, self)



    def verify(self, bolus = None, rate = None, units = None):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read pump settings
        self.read()

        # Check if pump is ready to take action
        if bolus is not None:

            if bolus > self.values["Max Bolus"]:

                # Give user info
                print ("Pump cannot issue bolus since it is bigger than its " +
                       "maximal allowed bolus. Update the latter before " +
                       "trying again." )

                return False

        elif (rate is not None) and (units is not None):

            if ((units == "U/h") and (rate > self.values["Max Basal"]) or
                (units == "%") and (rate > 200)):

                # Give user info
                print ("Pump cannot issue TBR since it is " +
                       "bigger than its maximal basal rate. Update the " +
                       "latter before trying again.") 

                return False

        # Give user info
        print "Pump's settings allow desired course of action. Proceeding..."

        return True



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare command
        self.command.prepare()

        # Do command
        self.command.do()

        # Store pump settings to profile report
        Reporter.storeSettings(self.values)

        # Give user info
        print "Pump settings: " + str(self.values)



class Unit(object):

    def __init__(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize value
        self.value = None



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare command
        self.command.prepare()

        # Do command
        self.command.do()

        # Show user units
        self.show()



    def show(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SHOW
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get unit name
        unit = self.__class__.__name__

        # Give user info
        print "Pump's '" + unit + "' set to: " + self.value



class BGU(Unit):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize units
        super(self.__class__, self).__init__()

        # Link with its respective command
        self.command = commands.ReadPumpBGU(pump, self)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read units
        super(self.__class__, self).read()

        # Store BG units to pump report
        Reporter.storeBGU(self.value)



class CU(Unit):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize units
        super(self.__class__, self).__init__()

        # Link with its respective command
        self.command = commands.ReadPumpCU(pump, self)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read units
        super(self.__class__, self).read()

        # Store BG units to pump report
        Reporter.storeCU(self.value)



class TBRU(Unit):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize units
        super(self.__class__, self).__init__()

        # Link with its respective command
        self.command = commands.SetPumpTBRU(pump, self)

        # Link with pump
        self.pump = pump



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read current TBR in order to extract current units
        self.pump.TBR.read()

        # Get units
        self.value = self.pump.TBR.value["Units"]

        # Show user units
        self.show()



    def set(self, units):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare command
        self.command.prepare(units)

        # Do command
        self.command.do()



class BGTargets(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize BG targets, times, and units
        self.values = []
        self.times = []
        self.units = None

        # Link with its respective command
        self.command = commands.ReadPumpBGTargets(pump, self)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare command
        self.command.prepare()

        # Do command
        self.command.do()

        # Store BG targets to pump report
        Reporter.storeBGTargets(self.times, self.values, self.units)

        # Store BG units to pump report
        Reporter.storeBGU(self.units)

        # Get number of BG targets read
        n = len(self.values)

        # Give user info
        print "Found " + str(n) + " BG targets:"

        for i in range(n):
            print (self.times[i] + " - " + str(self.values[i]) + " " +
                                           str(self.units))



class ISF(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize insulin sensitivity factors, times, and units
        self.values = []
        self.times = []
        self.units = None

        # Link with its respective command
        self.command = commands.ReadPumpISF(pump, self)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare command
        self.command.prepare()

        # Do command
        self.command.do()

        # Store insulin sensitivities factors to pump report
        Reporter.storeISF(self.times, self.values, self.units + "/U")

        # Store BG units to pump report
        Reporter.storeBGU(self.units)

        # Get number of ISF read
        n = len(self.values)

        # Give user info
        print "Found " + str(n) + " ISF:"

        for i in range(n):
            print (self.times[i] + " - " + str(self.values[i]) + " " +
                   self.units + "/U")



class CSF(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize carb sensitivity factors, times, and units
        self.values = []
        self.times = []
        self.units = None

        # Link with its respective command
        self.command = commands.ReadPumpCSF(pump, self)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare command
        self.command.prepare()

        # Do command
        self.command.do()

        # Store carb sensitivities factors to pump report
        Reporter.storeCSF(self.times, self.values, self.units + "/U")

        # Store BG units to pump report
        Reporter.storeCU(self.units)

        # Get number of ISF read
        n = len(self.values)

        # Give user info
        print "Found " + str(n) + " CSF:"

        for i in range(n):
            print (self.times[i] + " - " + str(self.values[i]) + " " +
                   self.units + "/U")



class DailyTotals(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize daily totals dictionary
        self.values = {"Today": None, "Yesterday": None}

        # Link with its respective command
        self.command = commands.ReadPumpDailyTotals(pump, self)



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare command
        self.command.prepare()

        # Do command
        self.command.do()

        # Give user info
        print "Daily totals:"
        print json.dumps(self.values, indent = 2, separators = (",", ": "),
                                      sort_keys = True)



class History(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize pump history vector
        self.pages = []

        # Link with its respective command
        self.commands = {"Measure": commands.MeasurePumpHistory(pump, self),
                         "Read": commands.ReadPumpHistory(pump, self)}

        # Link with all possible records
        self.records = {"Suspend": records.SuspendRecord(pump),
                        "Resume": records.ResumeRecord(pump),
                        "Bolus": records.BolusRecord(pump),
                        "Carbs": records.CarbsRecord(pump)}



    def measure(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            MEASURE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare command
        self.commands["Measure"].prepare()

        # Do command
        self.commands["Measure"].do()

        # Give user info
        print "Found " + str(self.size) + " pump history pages."



    def read(self, n = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # If no number of pages to read was specified, read all of them
        if not n:

            # Find number of existing history pages
            self.measure()

            # Assign number of pages found
            n = self.size

        # Download n most recent pages of pump history
        for i in range(n):

            # Prepare command
            self.commands["Read"].prepare(i)

            # Do command
            self.commands["Read"].do()

            # Get data
            data = self.commands["Read"].get()

            # Extend known history of pump
            self.pages.extend(data)

        # Compute number of bytes read
        size = len(data)

        # Print collected history pages
        print "Read " + str(n) + " page(s) [or " + str(size) + " byte(s)]:"
        print self.pages

        # Decode history pages
        self.decode()


    def decode(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DECODE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Give user info
        print "Decoding pump history..."

        # Find records within pump's history pages
        for i in self.records:
            self.records[i].find()

        # Store decoded records
        self.store()



    def store(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            STORE
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Store suspend times
        # FIXME

        # Store resume times
        # FIXME

        # Get boluses
        boluses = self.records["Bolus"]

        # Store boluses
        Reporter.addBoluses(boluses.times, boluses.values)

        # Get carbs
        carbs = self.records["Carbs"]

        # Store carbs
        Reporter.addCarbs(carbs.times, carbs.values)



class Bolus(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize bolus characteristics
        self.stroke = 0.1  # Pump bolus stroke (U)
        self.rate   = 40.0 # Bolus delivery rate (s/U)
        self.delay  = 5    # Time (s) to wait after bolus delivery

        # Link with its respective command
        self.command = commands.DeliverPumpBolus(pump, self)

        # Link with pump
        self.pump = pump



    def verify(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            VERIFY
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Get pump history
        history = self.pump.history

        # Read number of pump history pages
        history.measure()

        # If only one history page, read and search it for boluses
        if history.size == 1:
            history.read(1)

        # Otherwise, read last two pages
        else:
            history.read(2)



    def deliver(self, bolus):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            DELIVER
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        TODO: Check if last bolus stored fits to the one just delivered
        """

        # Verify pump status and settings before doing anything
        if not self.pump.status.verify():
            return

        if not self.pump.settings.verify(bolus):
            return

        # Compute time required for bolus to be delivered (giving it some
        # additional seconds to be safe)
        time = (self.rate * bolus + self.delay)

        # Prepare command
        self.command.prepare(bolus, self.stroke, time)

        # Do command
        self.command.do(False)

        # Verify if last bolus was correctly enacted # FIXME
        self.verify()



class TBR(object):

    def __init__(self, pump):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            INIT
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Initialize basal characteristics
        self.stroke = 0.05 # Pump basal stroke rate (U/h)
        self.timeBlock = 30 # Time block (m) used by pump for basal durations

        # Define current TBR dictionary
        self.value = {"Rate": None,
                      "Units": None,
                      "Duration": None}

        # Link with its respective command
        self.commands = {"Read": commands.ReadPumpTBR(pump, self),
                         "Set": commands.SetPumpTBR(pump, self)}

        # Link with pump
        self.pump = pump



    def read(self):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            READ
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Prepare command
        self.commands["Read"].prepare()

        # Do command
        self.commands["Read"].do()

        # Give user info
        print "Current TBR:"
        print json.dumps(self.value, indent = 2,
                                     separators = (",", ": "),
                                     sort_keys = True)



    def set(self, rate, units, duration, cancel = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            SET
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Stringify TBR
        stringTBR = str(rate) + " " + units + " (" + str(duration) + "m)"

        # Give user info regarding the next TBR that will be set
        print ("Trying to set new TBR: " + stringTBR)

        # First run: check and make sure TBR can be set on pump!
        if not cancel:

            # Verify pump status and settings before doing anything
            if not self.pump.status.verify():
                return

            if not self.pump.settings.verify(rate = rate, units = units):
                return

            # Before issuing any TBR, read the current one
            self.read()

            # Store current TBR
            TBR = self.value

            # Look if a TBR is already set
            if TBR["Duration"] != 0:

                # Give user info
                print ("TBR must be canceled before issuing a new one...")

                # Cancel TBR
                self.cancel(TBR["Units"])

            # Look if units match up
            if units != TBR["Units"]:

                # Give user info
                print "Old and new TBR units do not match. Adjusting them..."

                # Modify units as wished by the user
                self.pump.units["TBR"].set(units)



        # Set TBR
        # Get current time
        now = datetime.datetime.now()

        # Format time at which TBR is requested
        now = lib.formatTime(now)

        # Prepare command
        self.commands["Set"].prepare(rate, units, duration)

        # Do command
        self.commands["Set"].do()

        # Give user info
        print "Verifying if new TBR was correctly set..."

        # Verify that the TBR was correctly issued by reading current TBR on
        # pump
        self.read()

        # Store current TBR
        TBR = self.value

        # Compare to expectedly set TBR
        if ((TBR["Rate"] == rate) and
            (TBR["Units"] == units) and
            (TBR["Duration"] == duration)):

            # Give user info
            print "New TBR correctly set: " + stringTBR
            print "Storing it..."

            # Add bolus to insulin report
            Reporter.addTBR(now, rate, units, duration)

        # Otherwise, quit
        else:

            # Raise error
            raise errors.TBRFail(stringTBR)



    def cancel(self, units = False):

        """
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CANCEL
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

        # Read units if not already provided
        if not units:

            # Read current units
            self.pump.units["TBR"].read()

            # Store them
            units = self.pump.units["TBR"].value

        # Cancel on-going TBR
        if units == "U/h":
            self.set(0, units, 0, True)

        elif units == "%":
            self.set(100, units, 0, True)



def main():

    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        MAIN
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    # Instanciate a pump for me
    pump = Pump()

    # Start dialogue with pump
    pump.start()

    # Read pump time
    #pump.time.read()

    # Read pump model
    #pump.model.read()

    # Read pump firmware version
    #pump.firmware.read()

    # Read pump battery level
    pump.battery.read()

    # Read remaining amount of insulin in pump
    #pump.reservoir.read()

    # Read pump status
    #pump.status.read()
    #pump.status.verify()
    #pump.status.suspend()
    #pump.status.resume()

    # Read pump settings
    #pump.settings.read()
    #pump.settings.verify()

    # Push button on pump
    #pump.buttons.push("EASY")
    #pump.buttons.push("ESC")
    #pump.buttons.push("ACT")
    #pump.buttons.push("UP")
    #pump.buttons.push("DOWN")

    # Read BG units set in pump's bolus wizard
    #pump.units["BG"].read()

    # Read carb units set in pump's bolus wizard
    #pump.units["C"].read()

    # Read current TBR units
    #pump.units["TBR"].read()

    # Read BG targets stored in pump
    #pump.BGTargets.read()

    # Read insulin sensitivity factors stored in pump
    #pump.ISF.read()

    # Read carb sensitivity factors stored in pump
    #pump.CSF.read()

    # Read daily totals on pump
    #pump.dailyTotals.read()

    # Read pump history
    #pump.history.read()

    # Send bolus to pump
    #pump.bolus.deliver(0.1)

    # Read current TBR
    #pump.TBR.read()

    # Send TBR to pump
    #pump.TBR.set(5, "U/h", 30)
    #pump.TBR.set(50, "%", 90)
    #pump.TBR.cancel()

    # Stop dialogue with pump
    pump.stop()



# Run this when script is called from terminal
if __name__ == "__main__":
    main()
