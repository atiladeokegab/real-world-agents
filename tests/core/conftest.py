def pytest_configure(config):
    config.addinivalue_line("markers", "slow: real end-to-end case, run only with RUN_SLOW=1")
