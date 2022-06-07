import random

from taxisim.human import Human
from taxisim.human import State as HumanState
from taxisim.point import Point
from taxisim.taxi.ride import Ride


def rand_point() -> Point:
    coords = [random.random() for _ in range(3)]
    return Point.from_array(coords)


def test_human_invited_states():
    human = Human("Albert", rand_point(), 100)
    friend = Human("Ricardo", rand_point(), 500)
    ride = Ride(rand_point(), rand_point(), passenger=human)

    assert human.state == HumanState.Rest
    human.feel_lonely()
    assert human.state == HumanState.WannaParty
    human.invited_by(friend)
    assert human.state == HumanState.OrderingCar
    assert human.friend == friend
    assert not human.is_host
    assert human.is_at_home
    assert not human.is_in_ride
    human.ordered_ride(ride)
    assert human.state == HumanState.AwaitingRide
    assert human.is_in_ride
    assert human.ride == ride
    human.car_arrived()
    assert human.state == HumanState.Ride
    human.arrived()
    assert human.state == HumanState.Party
    assert human.pos == friend.home
    assert not human.is_in_ride
    human.tired()
    assert human.state == HumanState.AwaitingRide
    assert not human.is_at_home
    human.ordered_ride(ride)
    assert human.state == HumanState.AwaitingRide
    assert human.is_in_ride
    assert human.ride == ride
    human.car_arrived()
    assert human.state == HumanState.Ride
    human.arrived()
    assert human.state == HumanState.Rest
    assert human._friend is None
    assert human._is_host is None
    assert human._ride is None
    assert human.is_at_home


def test_human_host_states():
    human = Human("Albert", rand_point(), 100)
    guest = Human("Ricardo", rand_point(), 500)

    assert human.state == HumanState.Rest
    human.feel_lonely()
    assert human.state == HumanState.WannaParty
    human.host_party(guest)
    assert human.state == HumanState.WaitGuest
    assert human.friend == guest
    assert human.is_host
    assert human.is_at_home
    human.guest_arrived()
    assert human.state == HumanState.Party
    human.tired()
    assert human.state == HumanState.Rest
    assert human._friend is None
    assert human._is_host is None
    assert human._ride is None
    assert human.is_at_home
