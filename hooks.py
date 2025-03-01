import django
import OPi.GPIO as GPIO
import orangepi.one
import time
import os
import logging

from django.utils import timezone
from app.models import Settings, CoinSlot, Rates, Ledger, CoinQueue

# Configure logging
logging.basicConfig(filename='coin_slot_listener.log', level=logging.ERROR)

GPIO.setmode(orangepi.one.BOARD)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'opw.settings')
django.setup()

COINSLOT_ID = 'dc1393af-9bad-422b-968b-69b869dfa4fe'

class CoinSlotListener:
    def __init__(self, input_pin, light_pin):
        self.input_pin = input_pin
        self.light_pin = light_pin
        self.start_time = time.perf_counter()
        self.pulse_count = 0
        self.max_elapsed_time = 0.5

    def pulse_detected(self, ready=False):
        if ready:
            self.start_time = time.perf_counter()
            self.pulse_count += 1

    def process(self):
        current_time = time.perf_counter()
        elapsed_time = current_time - self.start_time

        if GPIO.input(self.light_pin) and elapsed_time > self.max_elapsed_time:
            if self.pulse_count > 0:
                built_in_payment(COINSLOT_ID, self.pulse_count)
                self.start_time = current_time
                self.pulse_count = 0

def built_in_payment(identifier, pulse):
    try:
        slot = CoinSlot.objects.select_related('Client').get(Slot_ID=identifier)
        rates = Rates.objects.get(Pulse=pulse)

        if slot.is_available:
            return False

        ledger = Ledger(Client=slot.Client, Denomination=rates.Denom, Slot_No=slot.pk)
        ledger.save()

        q, _ = CoinQueue.objects.get_or_create(Client=slot.Client)
        q.Total_Coins += rates.Denom
        q.save()

        slot.Last_Updated = timezone.now()
        slot.save()

        return True

    except (CoinSlot.DoesNotExist, Rates.DoesNotExist) as e:
        logging.error(f"Payment error: {e}")
        return False

if __name__ == '__main__':
    setting = Settings.objects.get(pk=1)

    input_pin = setting.Coinslot_Pin
    light_pin = setting.Light_Pin

    GPIO.setwarnings(False)
    GPIO.setup(input_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(light_pin, GPIO.OUT, initial=GPIO.LOW)

    print('Started Listening to Coinslot')

    listener = CoinSlotListener(input_pin, light_pin)
    GPIO.add_event_detect(input_pin, GPIO.RISING, callback=lambda x: listener.pulse_detected(GPIO.input(light_pin)))

    while True:
        listener.process()
        time.sleep(0.005)
