import django
import OPi.GPIO as GPIO
import orangepi.one
import time, os

from django.utils import timezone
from datetime import timedelta
GPIO.setmode(orangepi.one.BOARD)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'opw.settings')
django.setup()

from app.models import Settings, CoinSlot, Rates, Ledger, CoinQueue

COINSLOT_ID = 'dc1393af-9bad-422b-968b-69b869dfa4fe'

def built_in_payment(identifier, pulse):
	try:
		slot = CoinSlot.objects.get(Slot_ID=identifier)
		rates = Rates.objects.get(Pulse=pulse)

		if slot.is_available:
			return False

		ledger = Ledger()
		ledger.Client = slot.Client
		ledger.Denomination = rates.Denom
		ledger.Slot_No = slot.pk
		ledger.save()

		q, _ = CoinQueue.objects.get_or_create(Client=slot.Client)
		q.Total_Coins += rates.Denom
		q.save()

		slot.Last_Updated = timezone.now()
		slot.save()

		return True

	except (CoinSlot.DoesNotExist, Rates.DoesNotExist):
		return False

def pulse_detected(ready=False):
	global start_time
	global pulse_count

	if not ready:
		return False

	start_time = time.time()
	pulse_count += 1

if __name__ == '__main__':
	setting = Settings.objects.get(pk=1)

	input_pin = setting.Coinslot_Pin
	light_pin = setting.Light_Pin

	GPIO.setwarnings(False)
	GPIO.setup(input_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(light_pin, GPIO.OUT, initial=GPIO.LOW)

	print('Started Listening to Coinslot')
	start_time = time.time()

	pulse_count = 0
	max_elapsed_time = .5

	GPIO.add_event_detect(input_pin, GPIO.RISING, callback=lambda x: pulse_detected(GPIO.input(light_pin)))

	if __name__ == '__main__':
		try:		
			while True:
				if GPIO.input(light_pin):
					elapsed_time = time.time() - start_time
					if pulse_count > 0 and elapsed_time > max_elapsed_time:
						built_in_payment(COINSLOT_ID, pulse_count)
						start_time = time.time()
						pulse_count = 0

				time.sleep(.01)

		except Exception as e:
			print('Error: ' + str(e))
		finally:
			GPIO.cleanup()
