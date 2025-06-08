""" The credits of the player, earned with missions and ore, spent on the
parts of the ship """


class Wallet:

    def __init__(self, credits: int = 0) -> None:
        self.credits = credits

    def can_pay(self, amount: int) -> bool:
        return self.credits >= amount

    def pay(self, amount: int) -> None:
        if not self.can_pay(amount):
            raise ValueError(f'{amount} credits, {self.credits} left')
        self.credits -= amount

    def earn(self, amount: int) -> None:
        self.credits += amount
