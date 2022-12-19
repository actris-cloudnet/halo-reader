class FileEmpty(Exception):
    pass


class HeaderNotFound(Exception):
    pass


class UnexpectedDataTokens(Exception):
    pass


class MergeError(Exception):
    pass


class NetCDFWriteError(Exception):
    pass
