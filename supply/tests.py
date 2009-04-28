from rapidsms.tests.scripted import TestScript
from apps.form.models import *
from apps.reporters.models import *
import apps.reporters.app as reporter_app
import apps.nigeria.app as nigeria_app
import apps.form.app as form_app
from app import App
from models import *
from django.core.management.commands.dumpdata import Command
import random
import time
from datetime import datetime, timedelta

class TestApp (TestScript):
    apps = (reporter_app.App, App,form_app.App, nigeria_app.App )
    # the test_backend script does the loading of the dummy backend that allows reporters
    # to work properly in tests
    fixtures = ['nigeria_llin', 'kano_locations', 'test_backend']
    
    def setUp(self):
        TestScript.setUp(self)
        
    def testFixture(self): 
        """"This isn't actually a test.  It just takes advantage
            of the test harness to spam a bunch of messages to the 
            supply app and spit out the data in a format that can
            be sucked into a fixture"""
        # this is the number of transactions that will be generated
        transaction_count = 0
        
        # these are the locations that will be the origins, chosen randomly
        # from this list
        # the destinations will be chosen randomly from the origins' children
        originating_locations = [20, 2001, 2002, 2003,2004]
        stock_levels = dict([[loc, random.randint(1, 10000) * 10 + 50000] for loc in originating_locations])
            
        
        # the sender will always be the same, for now
        phone = "55555"
        all_txns = []
        # these are the percentages these items will match
        waybill_match_percent = .9
        amount_match_percent = .9
        loc_match_percent = .95
        num_locs = len(Location.objects.all())
        
        # allow specifying the minimum and maximum dates for message generation
        min_date = datetime(2009,4,1)
        max_date = datetime(2009,4,30)
        min_time = time.mktime(min_date.timetuple())
        max_time = time.mktime(max_date.timetuple())
        
        # generate the array of dates we're going to use at the start.  This is so we can order 
        # our transactions
        iss_dates = []
        for i in range(transaction_count):
            iss_dates.append(datetime.fromtimestamp(random.randint(min_time, max_time)))
        iss_dates.sort()
        rec_dates = []
        for i in range(transaction_count):
            # make the date from a min and max timestamp
            rec_dates.append(datetime.fromtimestamp(
                random.randint(
                   # the min is the shipment date
                   time.mktime(iss_dates[i].timetuple()), 
                   #the max is the shipment date + 0 to 4 days
                   time.mktime((iss_dates[i] + timedelta(random.randint(0,4))).timetuple()))))
        
        for i in range(transaction_count):
            # get some random data based on the parameters we've set above
            origin = Location.objects.get(code=random.choice(originating_locations ))
            destination = random.choice(origin.children.all())
            waybill = random.randint(10000,99999)
            amount = random.randint(1, 500) * 10
            diff = stock_levels[int(origin.code)] - amount 
            if diff > 0:
                stock = diff
            else:
                stock = random.randint(1, 10000) * 10
            stock_levels[int(origin.code)] = stock
            issue_string = "%s@%s > llin issue from %s to %s %s %s %s" % (phone, iss_dates[i].strftime("%Y%m%d%H%M"), origin.code, destination.code, waybill, amount, stock)
            all_txns.append(issue_string)
            # create a waybill number based on the likelihood of match
            if random.random() < waybill_match_percent:
                ret_waybill = waybill
            else:
                ret_waybill = random.randint(10000,99999)
            # create an amount based on the likelihood of match
            if random.random() < amount_match_percent:
                ret_amount = amount
            else:
                ret_amount = random.randint(1, 500) * 10
            # create an origin and destination based on the likelihood of match
            if random.random() < loc_match_percent:
                ret_orig = origin
            else:
                ret_orig = Location.objects.get(pk=random.randint(1,num_locs))
            if random.random() < loc_match_percent:
                ret_dest = destination
            else:
                ret_dest = Location.objects.get(pk=random.randint(1, num_locs))
            if stock_levels.has_key(int(ret_dest.code)):
                ret_stock = stock_levels[int(ret_dest.code)] + amount
            else: 
                # make sure the stock at the receiver is higher than the amount of the bill
                ret_stock = random.randint(1, 2000) * 10 + ret_amount
            stock_levels[int(ret_dest.code)] = ret_stock
            # make sure the date received is after the date sent
            receive_string = "%s@%s > llin receive from %s to %s %s %s %s" % (phone, rec_dates[i].strftime("%Y%m%d%H%M"), ret_orig.code, ret_dest.code, ret_waybill, ret_amount, ret_stock)
            all_txns.append(receive_string)
            
        script = "\n".join(all_txns)
        self.runScript(script)
        dumpdata = Command()
        print "\n\n=========This is your fixture.  Copy and paste it to a text file========\n\n"
        print dumpdata.handle("supply")
        
    def testScript(self):
        mismatched_amounts = """
            8005552222 > llin register 20 sm mister sender 
            8005552222 < Hello mister! You are now registered as Stock manager at KANO State.
            8005551111 > llin register 2027 sm mister recipient
            8005551111 < Hello mister! You are now registered as Stock manager at KURA LGA.
            8005552222 > llin issue from 20 to 2027 11111 200 1800
            8005552222 < Received report for LLIN issue: origin=KANO, dest=KURA, waybill=11111, amount=200, stock=1800. If this is not correct, reply with CANCEL
            8005551111 > llin receive from 20 to 2027 11111 150 500
            8005551111 < Received report for LLIN receive: origin=KANO, dest=KURA, waybill=11111, amount=150, stock=500. If this is not correct, reply with CANCEL
            """
        self.runScript(mismatched_amounts)

        sender = Reporter.objects.get(alias="msender")
        recipient = Reporter.objects.get(alias="mrecipient")

        issue = PartialTransaction.objects.get(origin__name="KANO",\
           destination__name="KURA", shipment_id="11111",\
           domain__code__abbreviation="LLIN", type="I", reporter__pk=sender.pk)

        receipt = PartialTransaction.objects.get(origin__name__iexact="KANO",\
           destination__name__iexact="KURA", shipment_id="11111",\
           domain__code__abbreviation__iexact="LLIN", type="R", reporter__pk=recipient.pk)
        
        origin_stock = Stock.objects.get(location__name__iexact="KANO",\
            domain__code__abbreviation__iexact="LLIN")
        dest_stock = Stock.objects.get(location__name__iexact="KURA",\
            domain__code__abbreviation__iexact="LLIN")
        
        # everything in its right place
        self.assertEqual(sender.location, issue.origin)
        self.assertEqual(recipient.location, issue.destination)
        self.assertEqual(sender.location, receipt.origin)
        self.assertEqual(recipient.location, receipt.destination)

        # stocks created with correct balance
        self.assertEqual(issue.stock, origin_stock.balance)
        self.assertEqual(receipt.stock, dest_stock.balance)

        # issue and receipt have been matched into a transaction
        self.assertEqual(issue.status, 'C')
        self.assertEqual(issue.status, receipt.status)
        first_transaction = Transaction.objects.get(domain__code__abbreviation__iexact="LLIN",\
            amount_sent=issue.amount, amount_received=receipt.amount,\
            issue=issue, receipt=receipt)

        # mister recipient received 50 fewer nets than were sent by mister sender
        self.assertNotEqual(issue.amount, receipt.amount)
        self.assertNotEqual(first_transaction.amount_sent, first_transaction.amount_received)
        self.assertEqual(first_transaction.flag, 'A') 

        # mister recipient realizes his error and resends with correct amount
        amendment = """
            8005551111 > llin receive from 20 to 2027 11111 200 500
            8005551111 < Received report for LLIN receive: origin=KANO, dest=KURA, waybill=11111, amount=200, stock=500. If this is not correct, reply with CANCEL
            """
        self.runScript(amendment)

        # pick fresh sprouts of these from the database
        receipt = PartialTransaction.objects.get(pk=receipt.pk)
        first_transaction = Transaction.objects.get(pk=first_transaction.pk)

        # mister recipient's original receipt should now be amended and
        # the first transaction should be flagged as incorrect
        self.assertEqual(receipt.status, 'A')
        self.assertEqual(first_transaction.flag, 'I')

        # mister recipient's amendment
        second_receipt = PartialTransaction.objects.get(origin__name__iexact="KANO",\
           destination__name__iexact="KURA", shipment_id="11111",\
           domain__code__abbreviation__iexact="LLIN", type="R", reporter=recipient, status="C")

        # make sure this is a new one
        self.assertNotEqual(second_receipt.pk, receipt.pk)

        # make sure a new transaction was matched
        second_transaction = Transaction.objects.get(domain__code__abbreviation__iexact="LLIN",\
            amount_sent=issue.amount, amount_received=second_receipt.amount,\
            issue=issue, receipt=second_receipt)

        # make sure this is a new one
        self.assertNotEqual(first_transaction.pk, second_transaction.pk)

        # the new transaction should not be flagged with either of these
        self.assertNotEqual(second_transaction.flag, 'I')
        self.assertNotEqual(second_transaction.flag, 'A')

        # new figures should add up
        self.assertEqual(issue.amount, second_receipt.amount)
        self.assertEqual(second_transaction.amount_sent, second_transaction.amount_received)

    def testUnregisteredSubmissions(self):
        # send a form from an unregistered user and assure it is accepted
        unregistered_submission = """
            supply_tus_1 > llin issue from 20 to 2027 11111 200 1800
            supply_tus_1 < Received report for LLIN issue: origin=KANO, dest=KURA, waybill=11111, amount=200, stock=1800. If this is not correct, reply with CANCEL
            supply_tus_1 < Please register your phone.
            """
        self.runScript(unregistered_submission)
        
        # check that the connection object in the transaction is set properly
        connection = PersistantConnection.objects.get(identity="supply_tus_1")
        issue = PartialTransaction.objects.get(origin__name="KANO",\
           destination__name="KURA", shipment_id="11111",\
           domain__code__abbreviation="LLIN", type="I", connection=connection)
        
        # check that the reporter is empty
        self.assertFalse(issue.reporter)