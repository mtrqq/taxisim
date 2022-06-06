import pytest
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
    assert human.is_host == False
    assert human.is_at_home == True
    assert human.is_in_ride == False
    human.ordered_ride(ride)
    assert human.state == HumanState.AwaitingRide
    assert human.is_in_ride == True
    assert human.ride == ride
    human.car_arrived()
    assert human.state == HumanState.Ride
    human.arrived()
    assert human.state == HumanState.Party
    assert human.pos == friend.home
    assert human.is_in_ride == False
    human.tired()
    assert human.state == HumanState.AwaitingRide
    assert human.is_at_home == False
    human.ordered_ride(ride)
    assert human.state == HumanState.AwaitingRide
    assert human.is_in_ride == True
    assert human.ride == ride
    human.car_arrived()
    assert human.state == HumanState.Ride
    human.arrived()
    assert human.state == HumanState.Rest
    assert human._friend == None
    assert human._is_host == None
    assert human._ride == None
    assert human.is_at_home == True

def test_human_host_states():
    human = Human("Albert", Point(), 100)
    guest = Human("Ricardo", Point(), 500)

    assert human.state == HumanState.Rest
    human.feel_lonely()
    assert human.state == HumanState.WannaParty
    human.host_party(guest)
    assert human.state == HumanState.WaitGuest
    assert human.friend == guest
    assert human.is_host == True
    assert human.is_at_home == True
    human.guest_arrived()
    assert human.state == HumanState.Party
    human.tired()
    assert human.state == HumanState.Rest
    assert human._friend == None
    assert human._is_host == None
    assert human._ride == None
    assert human.is_at_home == True
