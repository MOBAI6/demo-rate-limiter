# 项目协同规范 (Demo Teamwork)

1. 语言：Python 3.9+，严格使用类型注解 (Type Hints)。
2. 并发安全：所有共享状态必须有线程锁保护 (threading.Lock)。
3. 测试驱动：代码必须配备单元测试与多线程并发测试。
4. 提交规范：遵循 Conventional Commits (feat/test/docs)。
