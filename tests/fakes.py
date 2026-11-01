from typing import NamedTuple

from app.logic.world.space import Vec2


class FakeVector(NamedTuple):
    x: float
    y: float


class FakeBody:
    """ Stands for a cymunk Body: no collisions, step() moves it along its
    velocity """

    def __init__(
        self,
        position: Vec2 = (0., 0.),
        velocity: Vec2 = (0., 0.),
        angle: float = 0.
    ) -> None:
        self._position = FakeVector(*position)
        self._velocity = FakeVector(*velocity)
        self.angle = angle
        self.angular_velocity = 0.

    @property
    def position(self) -> FakeVector:
        return self._position

    @position.setter
    def position(self, value: Vec2) -> None:
        self._position = FakeVector(*value)

    @property
    def velocity(self) -> FakeVector:
        return self._velocity

    @velocity.setter
    def velocity(self, value: Vec2) -> None:
        self._velocity = FakeVector(*value)

    def step(self, dt: float) -> None:
        self._position = FakeVector(
            self._position.x + self._velocity.x * dt,
            self._position.y + self._velocity.y * dt,
        )
