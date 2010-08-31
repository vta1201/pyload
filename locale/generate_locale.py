#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import walk, remove
from os.path import join
from subprocess import call

###### Core

EXCLUDE = ["BeautifulSoup.py", "module/gui", "web/locale", "web/ajax", "web/cnl", "web/pyload", "setup.py"]
print "Generate core.pot"

f = open("includes.txt", "wb")
f.write("./pyLoadCore.py\n")

for path, dir, filenames in walk("./module"):
    if [True for x in EXCLUDE if x in path]: continue
    for file in filenames:
        if file.endswith(".py") and file not in EXCLUDE:
            f.write(join(path, file) + "\n")

f.close()

call(["xgettext", "--files-from=includes.txt", "--default-domain=core", "--from-code=utf-8",
     "--copyright-holder=pyLoad Team", "--package-name=pyLoad", "--package-version=0.4","--msgid-bugs-address='bugs@pyload.org'"])


f = open("core.po", "rb")
content = f.read()
f.close()
remove("core.po")
content = content.replace("charset=CHARSET", "charset=UTF-8")

f = open("locale/core.pot", "wb")
f.write(content)
f.close()

########## GUI

print "Generate gui.pot"

EXCLUDE = []

f = open("includes.txt", "wb")
f.write("./pyLoadGui.py\n")

for path, dir, filenames in walk("./module/gui"):
    if [True for x in EXCLUDE if x in path]: continue
    for file in filenames:
        if file.endswith(".py") and file not in EXCLUDE:
            f.write(join(path, file) + "\n")

f.close()

call(["xgettext", "--files-from=includes.txt", "--default-domain=gui", "--from-code=utf-8",
     "--copyright-holder=pyLoad Team", "--package-name=pyLoad", "--package-version=0.4","--msgid-bugs-address='bugs@pyload.org'"])


f = open("gui.po", "rb")
content = f.read()
f.close()
remove("gui.po")
content = content.replace("charset=CHARSET", "charset=UTF-8")

f = open("locale/gui.pot", "wb")
f.write(content)
f.close()


###### CLI

print "Generate cli.pot"

f = open("includes.txt", "wb")
f.write("./pyLoadCli.py\n")
f.close()

call(["xgettext", "--files-from=includes.txt", "--default-domain=cli", "--from-code=utf-8",
     "--copyright-holder=pyLoad Team", "--package-name=pyLoad", "--package-version=0.4","--msgid-bugs-address='bugs@pyload.org'"])


f = open("cli.po", "rb")
content = f.read()
f.close()
remove("cli.po")
content = content.replace("charset=CHARSET", "charset=UTF-8")

f = open("locale/cli.pot", "wb")
f.write(content)
f.close()

###### Setup

print "Generate setup.pot"

f = open("includes.txt", "wb")
f.write("./module/setup.py\n")
f.close()

call(["xgettext", "--files-from=includes.txt", "--default-domain=setup", "--from-code=utf-8",
     "--copyright-holder=pyLoad Team", "--package-name=pyLoad", "--package-version=0.4","--msgid-bugs-address='bugs@pyload.org'"])


f = open("setup.po", "rb")
content = f.read()
f.close()
remove("setup.po")
content = content.replace("charset=CHARSET", "charset=UTF-8")

f = open("locale/setup.pot", "wb")
f.write(content)
f.close()

### Web

print "TODO: Generate django.po with python manage.py makemessages --all --locale en"

call(["mv", "./module/web/locale/en/LC_MESSAGES/django.po", "./locale/django.pot"])

print
print "All finished."