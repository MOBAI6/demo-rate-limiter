"""Unit tests for TokenBucketLimiter rate limiter implementation."""

import threading
import time
from typing import List
import unittest

from token_bucket import TokenBucketLimiter


class TestTokenBucketLimiter(unittest.TestCase):
    """Test suite for TokenBucketLimiter covering functional and concurrency requirements."""

    def test_init_validation(self) -> None:
        """Verify initialization argument validations."""
        with self.assertRaises(ValueError):
            TokenBucketLimiter(capacity=0, refill_rate=10)
        with self.assertRaises(ValueError):
            TokenBucketLimiter(capacity=-1, refill_rate=10)
        with self.assertRaises(ValueError):
            TokenBucketLimiter(capacity=10, refill_rate=0)
        with self.assertRaises(ValueError):
            TokenBucketLimiter(capacity=10, refill_rate=-5)

        limiter: TokenBucketLimiter = TokenBucketLimiter(capacity=10, refill_rate=5)
        self.assertEqual(limiter.capacity, 10.0)
        self.assertEqual(limiter.refill_rate, 5.0)
        self.assertAlmostEqual(limiter.current_tokens, 10.0, places=1)

    def test_single_thread_consume_and_reject(self) -> None:
        """1. Test basic single-threaded token consumption, zero handling, and rejection."""
        limiter: TokenBucketLimiter = TokenBucketLimiter(capacity=5, refill_rate=0.0001)

        # Disallow negative tokens
        with self.assertRaises(ValueError):
            limiter.allow_request(-1)

        # 0 tokens request should always be allowed without consuming tokens
        self.assertTrue(limiter.allow_request(0))
        self.assertAlmostEqual(limiter.current_tokens, 5.0, places=1)

        # Consume 2 tokens
        self.assertTrue(limiter.allow_request(2))
        self.assertAlmostEqual(limiter.current_tokens, 3.0, places=1)

        # Consume remaining 3 tokens
        self.assertTrue(limiter.allow_request(3))
        self.assertLess(limiter.current_tokens, 1.0)

        # Reject when empty
        self.assertFalse(limiter.allow_request(1))

        # Reject when requested tokens exceed available tokens
        self.assertFalse(limiter.allow_request(10))

    def test_token_smooth_refill(self) -> None:
        """2. Test token smooth refill over time and maximum capacity clamp."""
        # 10 capacity, 20 tokens per second -> ~2 tokens replenished per 0.1s
        limiter: TokenBucketLimiter = TokenBucketLimiter(capacity=10, refill_rate=20)

        # Exhaust bucket
        self.assertTrue(limiter.allow_request(10))
        self.assertFalse(limiter.allow_request(1))

        # Sleep 0.15s -> expect ~3 tokens refilled
        time.sleep(0.15)
        self.assertTrue(limiter.allow_request(2))

        # Sleep 0.6s -> should refill fully up to capacity (capped at 10.0)
        time.sleep(0.6)
        self.assertLessEqual(limiter.current_tokens, 10.0)
        self.assertGreaterEqual(limiter.current_tokens, 9.9)

        # Can consume full capacity again
        self.assertTrue(limiter.allow_request(10))
        self.assertFalse(limiter.allow_request(1))

    def test_50_threads_high_concurrency_zero_oversell(self) -> None:
        """3. Test 50 threads concurrent contention ensuring accuracy and zero oversell."""
        capacity: int = 30
        thread_count: int = 50
        # Negligible refill rate to isolate initial capacity burst contention
        limiter: TokenBucketLimiter = TokenBucketLimiter(capacity=capacity, refill_rate=1e-6)

        barrier: threading.Barrier = threading.Barrier(thread_count)
        results: List[bool] = []
        lock: threading.Lock = threading.Lock()

        def worker() -> None:
            # Align all 50 threads to trigger allow_request simultaneously
            barrier.wait()
            granted: bool = limiter.allow_request(1)
            with lock:
                results.append(granted)

        threads: List[threading.Thread] = [threading.Thread(target=worker) for _ in range(thread_count)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        success_count: int = sum(1 for r in results if r)
        failure_count: int = sum(1 for r in results if not r)

        # Zero oversell verification:
        # Exactly 30 requests must succeed, and exactly 20 must be rejected
        self.assertEqual(len(results), thread_count)
        self.assertEqual(
            success_count,
            capacity,
            f"Zero oversell violated! Expected {capacity} grants, got {success_count}",
        )
        self.assertEqual(
            failure_count,
            thread_count - capacity,
            f"Expected {thread_count - capacity} rejections, got {failure_count}",
        )
        self.assertLess(limiter.current_tokens, 1.0)

    def test_concurrent_stress_continuous_traffic(self) -> None:
        """Extended stress test: 50 threads performing continuous concurrent requests."""
        thread_count: int = 50
        requests_per_thread: int = 20
        limiter: TokenBucketLimiter = TokenBucketLimiter(capacity=100, refill_rate=50)

        barrier: threading.Barrier = threading.Barrier(thread_count)
        success_list: List[int] = []
        lock: threading.Lock = threading.Lock()

        def worker() -> None:
            barrier.wait()
            local_success: int = 0
            for _ in range(requests_per_thread):
                if limiter.allow_request(1):
                    local_success += 1
                time.sleep(0.001)
            with lock:
                success_list.append(local_success)

        threads: List[threading.Thread] = [threading.Thread(target=worker) for _ in range(thread_count)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        total_success: int = sum(success_list)
        tokens: float = limiter.current_tokens

        # Verify state integrity under high concurrent contention
        self.assertGreaterEqual(tokens, 0.0)
        self.assertLessEqual(tokens, 100.0)
        self.assertGreater(total_success, 0)
        self.assertLessEqual(total_success, thread_count * requests_per_thread)


if __name__ == "__main__":
    unittest.main()
