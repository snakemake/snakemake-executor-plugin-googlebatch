from google.api_core import retry
from requests.exceptions import ReadTimeout


def google_cloud_retry(ex):
    """
    Retry a Google Cloud request.

    Given an exception from Google Cloud, determine if it's one in the
    listing of transient errors (determined by function
    google.api_core.retry.if_transient_error(exception)) or determine if
    triggered by a hash mismatch due to a bad download. This function will
    return a boolean to indicate if retry should be done, and is typically
    used with the google.api_core.retry.Retry as a decorator (predicate).

    Arguments:
      ex (Exception) : the exception passed from the decorated function
    Returns: boolean to indicate doing retry (True) or not (False)
    """
    # Most likely case is Google API transient error.
    if retry.if_transient_error(ex):
        return True

    # Timeouts should be considered for retry as well.
    if isinstance(ex, ReadTimeout):
        return True
    return False


def bytesto(bytes, to, bsize=1024):
    """
    Convert bytes to megabytes.

    bytes to mb: bytesto(bytes, 'm')
    bytes to gb: bytesto(bytes, 'g' etc.
    From https://gist.github.com/shawnbutts/3906915
    """
    levels = {"k": 1, "m": 2, "g": 3, "t": 4, "p": 5, "e": 6}
    answer = float(bytes)
    for _ in range(levels[to]):
        answer = answer / bsize
    return answer


def read_file(filename):
    """
    Read a file from the local system.
    """
    with open(filename, "r") as fd:
        content = fd.read()
    return content
