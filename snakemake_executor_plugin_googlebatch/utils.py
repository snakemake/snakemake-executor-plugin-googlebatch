
def read_file(filename):
    """
    Read a file from the local system.
    """
    with open(filename, 'r') as fd:
        content = fd.read()
    return content