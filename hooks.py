import django
import OPi.GPIO as GPIO
import orangepi.one
import time, os
GPIO.setmode(orangepi.one.BOARD)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'opw.settings')
django.setup()

from app.models import Settings
from app.tasks import built_in_payment

COINSLOT_ID = 'n8cy3oKCKM'

def pulse_detected():
	global start_time
	global pulse_count	
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

	GPIO.add_event_detect(input_pin, GPIO.RISING, pulse_detected)

	if __name__ == '__main__':
		try:		
			while True:
				if GPIO.input(light_pin):
					elapsed_time = time.time() - start_time
					if pulse_count > 0 and elapsed_time > max_elapsed_time:
						built_in_payment.delay(COINSLOT_ID, pulse_count)
						start_time = time.time()
						pulse_count = 0
				
				time.sleep(.01)

		except Exception as e:
			print('Error: ' + str(e))
		finally:
			GPIO.cleanup()
