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
    def get(self, block=True, timeout=None):
        ...

    def put(self, item, block=True, timeout=None):
        ...


class EventServer(Generic[EventType]):
    def __init__(
        self,
        handle,
        threads=1,
        interval=1.0,
        daemon=False,
        queue=None,
    ):
        self.handle = handle
        self._interval = interval
        self._stop = Event()
        self._events = queue if queue is not None else SimpleQueue()
        self._threads = [
            Thread(target=self.serve, daemon=daemon) for _ in range(threads)
        ]

    @property
    def is_alive(self):
        return any(thread.is_alive() for thread in self._threads)

    def start(self):
        if self.is_alive:
            raise RuntimeError("Server is already started")

        for thread in self._threads:
            thread.start()

    def shutdown(self, nowait=False):
        if not self.is_alive:
            raise RuntimeError("Server is not alive")

        self._stop.set()
        if not nowait:
            for thread in self._threads:
                thread.join()

    def serve(self):
        while not self._stop.is_set():
            try:
                event = self._events.get(timeout=self._interval)
                if not self.handle(event):
                    self._events.put(event, block=True)
            except queue.Empty:
                pass

    def emit(self, event):
        if self._stop.is_set():
            raise ServiceShutdownError("Event service is shutting down")

        self._events.put(event, block=True)
