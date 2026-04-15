from threading import Thread
from queue import Queue

from typing import Callable, Generic, Sequence, Iterable
import typing

T = typing.TypeVar("T")

# Exceptions
class WorkFinishedException(Exception): pass

# Base classes
class BaseWorker:
    def __init__(self, work_unit: Callable[[], None] | None = None):
        self.work_unit = work_unit

    def run(self):
        try:
            while True:
                self.do_work()
        except WorkFinishedException:
            pass


    # API
    def do_work(self):
        if self.work_unit is None:
            raise NotImplementedError()
        else:
            self.work_unit()


class BaseProducer(Generic[T]):
    def __init__(self, produce_unit: Callable[[],Iterable[T]] | None = None,):
        self.produce_unit = produce_unit

    # API
    def produce(self) -> Iterable[T]:
        if self.produce_unit is None:
            raise NotImplementedError()
        else:
            return self.produce_unit()


class BaseConsumer(Generic[T]):
    def __init__(self, consume_unit: Callable[[T], None] | None = None):
        self.consume_unit = consume_unit

    # API
    def consume(self, product: T, /):
        if self.consume_unit is None:
            raise NotImplementedError()
        else:
            return self.consume_unit(product)

# Thread running an infinte loop
class Worker(BaseWorker,Thread):
    def __init__(self, work_unit: Callable[[], None] | None = None, *, daemon=True):
        Thread.__init__(self,daemon=daemon)
        BaseWorker.__init__(self, work_unit)


class Producer(BaseProducer[T], Worker, Generic[T]):
    def __init__(self, queue: Queue[T], produce_unit: Callable[[],Iterable[T]] | None = None, *, daemon=True):
        BaseProducer.__init__(self, produce_unit)
        Worker.__init__(self, daemon=daemon)

        self.queue = queue

    def do_work(self):
        products = self.produce()
        for p in products: self.queue.put(p)


class Consumer(BaseConsumer[T], Worker, Generic[T]):
    def __init__(self, queue: Queue[T], consume_unit: Callable[[T], None] | None = None, *, daemon=True):
        BaseConsumer.__init__(self, consume_unit)
        Worker.__init__(self, daemon=daemon)

        self.queue = queue

    def do_work(self):
        product = self.queue.get()
        self.consume(product)



class WorkerPool:
    def __init__(self, workers: Sequence[Worker]):
        self.workers = workers

    def start(self):
        for worker in self.workers:
            worker.start()

    def join(self):
        for worker in self.workers:
            worker.join()


class LikeWorkerPool(BaseWorker, WorkerPool):
    def __init__(self, work_unit: Callable[[], None] | None = None, worker_count: int = 1, *, daemon=True):
        BaseWorker.__init__(self, work_unit)

        workers = [Worker(self.do_work, daemon=daemon) for _ in range(worker_count)]
        WorkerPool.__init__(self, workers)


class LikeConsumerProducerPool(BaseProducer[T], BaseConsumer[T], WorkerPool, Generic[T]):
    def __init__(self,
                 produce_unit: Callable[[],Iterable[T]] | None = None,
                 consume_unit: Callable[[T], None] | None = None,
                 producer_count: int = 1,
                 consumer_count: int = 1,
                 *,
                 daemon=True):

        BaseProducer.__init__(self, produce_unit)
        BaseConsumer.__init__(self, consume_unit)

        self._producer_count = producer_count
        self._consumer_count = consumer_count

        self._queue: Queue[T] = Queue()

        workers = []
        workers += [Producer(self._queue, self.produce, daemon=daemon) for _ in range(producer_count)]
        workers += [Consumer(self._queue, self.consume, daemon=daemon) for _ in range(consumer_count)]

        WorkerPool.__init__(self, workers)

    @property
    def producers(self):
        return self.workers[:self._producer_count]

    @property
    def consumers(self):
        return self.workers[self._producer_count:]


