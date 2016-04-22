from bundlebuilder import buildapp

buildapp(
        name = "QtPlaskin",
        mainprogram = "qtplaskin.py",
        resources = ["mainwindow.py", "zdplaskin.py", "runner.py",
                     "mplwidget.py", "modeldata.py"],
        iconfile='qtplaskin2.icns'
)
