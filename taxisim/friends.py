import enum
import queue
from dataclasses import dataclass
from queue import SimpleQueue
from typing import Any
from typing import Callable
from typing import Protocol

from taxisim.human import Human
from taxisim.service import EventServer


class Role(enum.Enum):
    Host = enum.auto()
    Guest = enum.auto()


@dataclass(frozen=True)
class FriendRequest:
    human: Human
    on_found: Callable[[Human, Role], None]


class FriendsServiceAPI(Protocol):
    def find_friend(self, me: Human, on_found: Callable[[Human], None]) -> None:
        ...


class FriendsService:
    def __init__(
        self,
        daemon: bool = True,
    ) -> None:
        self._requestsq: SimpleQueue[FriendRequest] = SimpleQueue()
        self._events = EventServer(
            self._handle_friend_request, daemon=daemon, queue=self._requestsq
        )

    def _handle_friend_request(self, request: FriendRequest) -> bool:
        try:
            match_req = self._requestsq.get_nowait()

            request.on_found(match_req.human, Role.Host)
            match_req.on_found(request.human, Role.Guest)
            return True
        except queue.Empty:
            return False

    def find_friend(self, me: Human, on_found: Callable[[Human, Role], None]) -> None:
        request = FriendRequest(human=me, on_found=on_found)
        self._events.emit(request)

    def start(self) -> None:
        self._events.start()

    def shutdown(self, nowait: bool = False) -> None:
        self._events.shutdown(nowait=nowait)

    def __enter__(self) -> "FriendsService":
        self.start()
        return self

    def __exit__(self, *_: Any) -> None:
        self.shutdown()
