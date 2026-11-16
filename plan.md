# 需求方案：线程安全令牌桶限流器 (Token Bucket Rate Limiter)

## 架构分工
- **CLI 1 (架构师 / agy / 账号1)**: 编写 `rate_limiter.py` 抽象基类 `RateLimiter`，定义 `allow_request(tokens=1) -> bool`。
- **CLI 2 (主力研发 / agy2 / 账号2)**: 编写 `token_bucket.py`，继承 `RateLimiter`，实现纳秒级平滑令牌生成与并发锁机制。
- **CLI 3 (质检安全 / agy3 / 账号3)**: 编写 `test_token_bucket.py`，覆盖基础限流、突发流量与多线程并发测试，并跑通验证。
