from gpiozero import Button
class button(Button):

    def __init__(self, pin):
        self.pin = pin
        self.button = Button(pin, bounce_time=0.1)
        self.pressed = False
        self.button.when_pressed = self.press
        self.button.when_released = self.release
    def set_False(self):
        self.pressed = False
    def press(self):
        self.pressed = True
    def release(self):
        self.pressed = False