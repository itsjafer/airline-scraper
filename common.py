class StandardFlight:
    def __init__(self, departureDateTime, arrivalDateTime, origin, destination, flightNo, duration, fares):
        self.departureDateTime = departureDateTime
        self.arrivalDateTime = arrivalDateTime
        self.origin = origin
        self.destination = destination
        self.flightNo = flightNo
        self.duration = duration
        self.fares = fares

    def __str__(self):
        return f"{self.flightNo}: {self.origin} on {self.departureDateTime} -> {self.destination} on {self.arrivalDateTime}. Fares: {self.fares}.\n"

    def __repr__(self):
        return f"{self.flightNo}: {self.origin} on {self.departureDateTime} -> {self.destination} on {self.arrivalDateTime}. Fares: {self.fares}.\n"

# Constants
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36"

VIEWPORT = { 'width': 1920, 'height': 1080 }
