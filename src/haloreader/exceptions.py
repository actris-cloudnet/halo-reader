class HaloException(Exception):
    pass


class FileEmpty(HaloException):
    pass


class HeaderNotFound(HaloException):
    pass


class UnexpectedDataTokens(HaloException):
    pass


class InconsistentRangeError(HaloException):
    pass


class MergeError(HaloException):
    pass


class NetCDFWriteError(HaloException):
    pass


class BackgroundReadError(HaloException):
    pass


class BackgroundCorrectionError(HaloException):
    pass
