size_of_file_two = 10


def walk(path):
    dirpath = "/test/"
    dirnames = ["dir_one", "dir_two"]
    filenames = ["file_one", "file_two", "file_three"]
    yield dirpath, dirnames, filenames


def getsize(path):
    if path == "/test/file_two":
        return size_of_file_two
    else:
        return 10
