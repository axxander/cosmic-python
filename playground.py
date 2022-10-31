def fn():
    print("entered fn")
    def _inner():
        print("in inner")

    return _inner

    yield _inner

    print("exited fn")