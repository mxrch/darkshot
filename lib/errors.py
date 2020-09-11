class TesseractNotFound(BaseException):
    """Raised when the Tesseract installation folder can't be found"""
    pass

class TessdataFolderNotFound(BaseException):
    """Raised when the Tesseract tessdata folder can't be found"""
    pass

class AlgoNotFound(BaseException):
    """Raised when the algorithm chosen can't be found"""
    pass

class RequestFailed(BaseException):
    """Raised when the request doesn't have the status_code attribute"""
    pass

class RequestIssue(BaseException):
    """Raised when the request doesn't have a 200 status code"""
    pass

class OcrLangNotFound(BaseException):
    """Raised when the OCR Lang was not found installed or in the git repo"""
    pass