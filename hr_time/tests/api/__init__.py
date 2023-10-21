import sys


class FakeLogger:
    @staticmethod
    def info(message):
        return

    def set_log_level(self, level):
        return


class FakeUtils:
    logger = FakeLogger()


class FakeFrappe(object):
    utils = FakeUtils()

    @staticmethod
    def logger(level, allow_site, file_count):
        return FakeLogger()


# noinspection PyTypeChecker
sys.modules["frappe"] = FakeFrappe
