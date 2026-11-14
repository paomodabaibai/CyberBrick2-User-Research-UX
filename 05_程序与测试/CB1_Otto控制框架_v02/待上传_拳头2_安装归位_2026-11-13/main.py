import os
if 'commissioning_hold' in os.listdir('/'):
    print('PUNCH2 INSTALLED; installation hold; no automatic PWM')
else:
    import second_punch_main
