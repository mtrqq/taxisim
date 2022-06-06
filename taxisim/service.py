import queue
from queue import SimpleQueue
from threading import Event
from threading import Thread
from typing import Callable
from typing import Generic
from typing import Protocol
from typing import TypeVar

EventType = TypeVar("EventType")
MessageType = TypeVar("MessageType")


class ServiceShutdownError(RuntimeError):
    pass


class QProto(Protocol[MessageType]):
    def get(self, block: bool = True, timeout: float = None) -> MessageType:
        ...

    def put(self, item: MessageType, block: bool = True, timeout: float = None):
        ...


class EventServer(Generic[EventType]):
    def __init__(
        self,
        handle: Callable[[EventType], bool],
        threads: int = 1,
        interval: float = 1.0,
        daemon: bool = False,
        queue: QProto[EventType] | None = None,
    ) -> None:
        self.handle = handle
        self._interval = interval
        self._stop = Event()
        self._events: QProto[EventType] = queue if queue is not None else SimpleQueue()
        self._threads: list[Thread] = [
            Thread(target=self.serve, daemon=daemon) for _ in range(threads)
        ]

    @property
    def is_alive(self) -> bool:
        return any(thread.is_alive() for thread in self._threads)

    def start(self) -> None:
        if self.is_alive:
            raise RuntimeError("Server is already started")

        for thread in self._threads:
            thread.start()

    def shutdown(self, nowait: bool = False) -> None:
        if not self.is_alive:
            raise RuntimeError("Server is not alive")

        self._stop.set()
        if not nowait:
            for thread in self._threads:
                thread.join()

    def serve(self) -> None:
        while not self._stop.is_set():
            try:
                event = self._events.get(timeout=self._interval)
                if not self.handle(event):
                    self._events.put(event, block=True)
            except queue.Empty:
                pass

    def emit(self, event: EventType) -> None:
        if self._stop.is_set():
            raise ServiceShutdownError("Event service is shutting down")

        self._events.put(event, block=True)
