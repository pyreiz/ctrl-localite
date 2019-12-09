from localite.mitm import ManInTheMiddle


def start():
    "Start the Localite-ManInTheMiddle as an independent process"
    Popen(["ctrl-localite"])


def ctrl():
    ManInTheMiddle().start()
