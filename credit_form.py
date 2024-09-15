from dataclasses import dataclass


@dataclass
class CreditForm:
    duration_month = None
    percent = None
    amount = None

    def print(self):
        print(self.duration_month)
        print(self.percent)
        print(self.amount)
