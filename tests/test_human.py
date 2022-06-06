from taxisim.human import Human
from taxisim.human import State as HumanState
from taxisim.point import Point
from taxisim.taxi.ride import Ride


def test_human_invited_states():
    human = Human("Albert", Point(), 100)
    friend = Human("Ricardo", Point(), 500)
    ride = Ride(Point(), Point(), passenger=human)

    assert human.state == HumanState.Rest
    human.feel_lonely()
    assert human.state == HumanState.WannaParty
    human.invited_by(friend)
    assert human.state == HumanState.AwaitingRide
    assert human.friend == friend
    assert human.is_host is False
    assert human.is_at_home is True
    assert human.is_in_ride is False
    human.ordered_ride(ride)
    assert human.state == HumanState.AwaitingRide
    assert human.is_in_ride is True
    assert human.ride == ride
    human.car_arrived()
    assert human.state == HumanState.Ride
    human.arrived()
    assert human.state == HumanState.Party
    assert human.pos == friend.home
    assert human.is_in_ride is False
    human.tired()
    assert human.state == HumanState.AwaitingRide
    assert human.is_at_home is False
    human.ordered_ride(ride)
    assert human.state == HumanState.AwaitingRide
    assert human.is_in_ride is True
    assert human.ride == ride
    human.car_arrived()
    assert human.state == HumanState.Ride
    human.arrived()
    assert human.state == HumanState.Rest
    assert human._friend is None
    assert human._is_host is None
    assert human._ride is None
    assert human.is_at_home is True


def test_human_host_states():
    human = Human("Albert", Point(), 100)
    guest = Human("Ricardo", Point(), 500)

    assert human.state == HumanState.Rest
    human.feel_lonely()
    assert human.state == HumanState.WannaParty
    human.host_party(guest)
    assert human.state == HumanState.WaitGuest
    assert human.friend == guest
    assert human.is_host is True
    assert human.is_at_home is True
    human.guest_arrived()
    assert human.state == HumanState.Party
    human.tired()
    assert human.state == HumanState.Rest
    assert human._friend is None
    assert human._is_host is None
    assert human._ride is None
    assert human.is_at_home is True
