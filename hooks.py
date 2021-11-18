import json, time, os, threading
from typing import Set
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'opw.settings')
import django
django.setup()

from app.models import Settings
from app.tasks import built_in_payment

try:
	import RPi.GPIO as GPIO
except:
	import OPi.GPIO as GPIO
	GPIO.setboard(GPIO.PCPCPLUS)

GPIO.setmode(GPIO.BOARD)

coinslot_id = 'n8cy3oKCKM'

if __name__ == '__main__':
	try:
		settings = Settings.objects.get(pk=1)
		while True:
			print('Started Listening to Coinslot')
			input_pin = settings.Coinslot_Pin
			light_pin = settings.Light_Pin
			Slot_Timeout = settings.Slot_Timeout

			GPIO.setup(input_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
			GPIO.setup(light_pin, GPIO.OUT, initial=GPIO.LOW)

			while True:
				light_status = GPIO.input(light_pin)

				if light_status == True:
					startTime = time.time()
					prev_state = True
					pulseCount = 0
					maxElapsedTime = .5
					sleepTime = .01

					while True:
						light_state = GPIO.input(light_pin)

						if light_state:
							state = GPIO.input(input_pin)
							if state == False and prev_state == True:
								startTime = time.time()
								pulseCount += 1
							else:
								elapsedTime = time.time() - startTime
								if elapsedTime > Slot_Timeout:
									GPIO.output(light_pin, GPIO.LOW)

								if elapsedTime > maxElapsedTime and pulseCount > 0:
									# insert_thread = threading.Thread(target=credit_pulse, args=[coinslot_id, pulseCount])
									# insert_thread.daemon = True
									# insert_thread.start()
									built_in_payment.delay()

									pulseCount = 0
									startTime = time.time()

							time.sleep(sleepTime)
							prev_state = state
						else:
							break

				time.sleep(1)

	except Exception as e:
		print('Error: ' + str(e))
	except Settings.DoesNotExist:
		print('Settings not found.')
	finally:
		GPIO.cleanup()
