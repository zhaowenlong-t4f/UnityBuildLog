"""预读取迭代器实现。

这个模块实现了一个预读取装饰器，可以对任何基础迭代器进行装饰，
为其添加异步预读取功能，以提高读取性能。
"""
from typing import Iterator, Optional, Generic, TypeVar
from queue import Queue, Empty as QueueEmpty, Full as QueueFull
import threading
from concurrent.futures import ThreadPoolExecutor
import time

T = TypeVar('T')

class PreFetchIterator(Generic[T]):
    """预读取迭代器的实现。
    
    这个类使用装饰器模式来增强现有的迭代器，添加预读取功能。
    它维护一个预读取队列，使用后台线程来预先读取数据。
    
    属性:
        base_iterator: 被装饰的基础迭代器
        prefetch_queue: 存储预读取数据的队列
        prefetch_size: 预读取队列的大小限制
        prefetch_thread: 执行预读取的后台线程
        _stop_event: 用于停止预读取线程的事件
        _worker_exception: 存储工作线程中发生的异常
    """
    
    def __init__(self, base_iterator: Iterator[T], prefetch_size: int = 3, timeout: float = 0.1):
        """初始化预读取迭代器。
        
        Args:
            base_iterator: 要增强的基础迭代器
            prefetch_size: 预读取队列的大小，默认为3
            timeout: 队列操作的超时时间，默认0.1秒
        """
        self.base_iterator = base_iterator
        self.prefetch_size = prefetch_size
        self.timeout = timeout
        
        # 优化1：使用更大的初始队列大小，以支持突发读取
        queue_size = max(prefetch_size * 2, 100)  # 至少100的缓冲区
        self.prefetch_queue: Queue[Optional[T]] = Queue(maxsize=queue_size)
        
        # 优化2：使用线程池进行批量预读取
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._futures = []
        
        # 添加性能监控计数器
        self._prefetch_count = 0
        self._fetch_count = 0
        self._last_queue_size = 0
        self._queue_full_count = 0
        self._queue_empty_count = 0
        self._last_check_time = time.time()
        
        # 增强线程同步机制
        self._stop_event = threading.Event()
        self._data_ready = threading.Event()
        self._batch_size = min(50, prefetch_size)  # 优化3：动态批处理大小
        self._worker_exception = None
        
        # 启动预读取线程
        self.prefetch_thread = threading.Thread(target=self._prefetch_worker)
        self.prefetch_thread.daemon = True
        self.prefetch_thread.start()
        
        # 优化4：初始预热，等待队列达到一定填充率
        warmup_timeout = min(timeout * 2, 1.0)
        self._data_ready.wait(timeout=warmup_timeout)
    
    def _batch_fetch(self, batch_size: int) -> list:
        """批量获取数据。
        
        Args:
            batch_size: 批量获取的大小
            
        Returns:
            list: 获取到的数据列表
        """
        items = []
        for _ in range(batch_size):
            try:
                items.append(next(self.base_iterator))
            except StopIteration:
                break
        return items

    def _prefetch_worker(self):
        """预读取工作线程的实现。
        
        这个方法在后台线程中运行，使用线程池进行批量预读取。
        实现了自适应的预读取机制和性能监控。
        """
        try:
            while not self._stop_event.is_set():
                try:
                    # 定期检查和调整预读取参数
                    current_time = time.time()
                    if current_time - self._last_check_time > 1.0:
                        self._adjust_prefetch_rate()
                        self._last_check_time = current_time

                    # 计算当前批次大小
                    queue_size = self.prefetch_queue.qsize()
                    available_space = self.prefetch_queue.maxsize - queue_size
                    if available_space < self._batch_size * 0.5:
                        # 队列接近满，减小批量大小
                        current_batch_size = max(1, self._batch_size // 4)
                    else:
                        # 正常批量大小
                        current_batch_size = self._batch_size

                    # 直接在主线程中批量获取数据
                    items = self._batch_fetch(current_batch_size)
                    
                    if not items:  # 没有新数据
                        self.prefetch_queue.put(None)
                        return

                    # 批量放入队列
                    for item in items:
                        while not self._stop_event.is_set():
                            try:
                                self.prefetch_queue.put(item, timeout=self.timeout)
                                self._prefetch_count += 1
                                self._data_ready.set()
                                break
                            except QueueFull:
                                self._queue_full_count += 1
                                # 使用动态休眠时间
                                sleep_time = min(
                                    self.timeout * (self._queue_full_count / 10),
                                    self.timeout
                                )
                                time.sleep(sleep_time)

                    # 短暂休眠以避免CPU过度使用
                    if self.prefetch_queue.full():
                        time.sleep(self.timeout)
                    elif self._queue_empty_count > 0:
                        # 如果之前出现过队列空，加快预读取
                        time.sleep(self.timeout * 0.1)
                    else:
                        time.sleep(self.timeout * 0.5)

                except StopIteration:
                    self.prefetch_queue.put(None)
                    break

        except Exception as e:
            self._worker_exception = e
            while not self._stop_event.is_set():
                try:
                    self.prefetch_queue.put(None, timeout=self.timeout)
                    break
                except QueueFull:
                    self._queue_full_count += 1
                    continue
        finally:
            self._data_ready.set()
            self._executor.shutdown(wait=False)

    def _adjust_prefetch_rate(self):
        """动态调整预读取参数。"""
        qsize = self.prefetch_queue.qsize()
        
        # 计算队列使用率变化
        queue_usage = qsize / self.prefetch_queue.maxsize
        size_change = qsize - self._last_queue_size
        self._last_queue_size = qsize
        
        # 基于使用率和变化趋势调整超时时间
        if queue_usage > 0.8 and self._queue_full_count > 0:
            # 队列经常满，增加超时时间
            self.timeout = min(self.timeout * 1.2, 1.0)
        elif queue_usage < 0.2 and self._queue_empty_count > 0:
            # 队列经常空，减少超时时间
            self.timeout = max(self.timeout * 0.8, 0.001)
            
        # 重置计数器
        self._queue_full_count = 0
        self._queue_empty_count = 0
    
    def __iter__(self):
        """返回迭代器自身。"""
        return self
    
    def __next__(self) -> T:
        """获取队列中的下一个元素。
        
        实现了自适应的消费机制，支持批量获取和性能监控。
        
        Returns:
            下一个元素
            
        Raises:
            StopIteration: 当迭代结束时
            Exception: 当工作线程发生异常时
        """
        while True:
            try:
                # 如果队列为空，重置数据就绪事件并等待
                if self.prefetch_queue.empty():
                    self._data_ready.clear()
                    self._queue_empty_count += 1
                    self._data_ready.wait(timeout=self.timeout)

                item = self.prefetch_queue.get_nowait()
                self._fetch_count += 1
                
                # 处理结束标记
                if item is None:
                    if self._worker_exception:
                        raise self._worker_exception
                    raise StopIteration
                    
                return item
                
            except QueueEmpty:
                # 检查工作线程是否还活着
                if not self.prefetch_thread.is_alive():
                    if self._worker_exception:
                        raise self._worker_exception
                    raise StopIteration
                self._queue_empty_count += 1
                continue
    
    def close(self):
        """关闭预读取迭代器，停止后台线程。"""
        self._stop_event.set()
        if hasattr(self.base_iterator, 'close'):
            self.base_iterator.close()