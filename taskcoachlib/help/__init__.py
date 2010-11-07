'''
Task Coach - Your friendly task manager
Copyright (C) 2004-2010 Task Coach developers <developers@taskcoach.org>

Task Coach is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Task Coach is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from taskcoachlib import meta
from taskcoachlib.i18n import _
from tips import showTips

_MSURL = "http://www.microsoft.com/downloadS/details.aspx?familyid=200B2FD9-AE1A-4A14-984D-389C36F85647&displaylang=en"

def sequence(*text):
    return ''.join(text)

def a_href(text, name):
    return '<a href="#%s">%s</a>'%(name, text)

def a_name(text, name):
    return '<a name="%s">%s</a>'%(name, text)

def h(level, text):
    return '<h%d>%s</h%d>'%(level, text, level)

def h3(text):
    return h(3, text)

def h4(text):
    return h(4, text)

def h5(text):
    return h(5, text)
    
def p(*text):
    return '<p>%s</p>'%'\n'.join(text)

def ul(*li):
    return '<ul>%s</ul>'%'\n'.join(li)

def li(*text):
    return '<li>%s</li>'%'\n'.join(text)

_TOC = sequence(
    h3(_('Table of contents')),
    ul(
        li(
            a_href(_('Tasks'), 'tasks'),
            ul(
                li(a_href(_('About tasks'), 'abouttasks')),
                li(a_href(_('Task properties'), 'taskproperties')),
                li(a_href(_('Task states'), 'taskstates')),
                li(a_href(_('Task colors'), 'taskcolor')))),
        li(
            a_href(_('Effort'), 'effort'),
            ul(
               li(a_href(_('About effort'), 'abouteffort')),
               li(a_href(_('Effort properties'), 'effortproperties')))),
        li(
            a_href(_('Categories'), 'categories'),
            ul(
                li(a_href(_('About categories'), 'aboutcategories')),
                li(a_href(_('Category properties'), 'categoryproperties')))),
        li(
            a_href(_('Notes'), 'notes'),
            ul(
                li(a_href(_('About notes'), 'aboutnotes')),
                li(a_href(_('Note properties'), 'noteproperties')))),
        li(
            a_href(_('Printing and exporting'), 'printingandexporting'),
            ul(
                li(a_href(_('About printing and exporting'), 
                          'aboutprintingandexporting')),
                li(a_href(_('Printing'), 'printing')),
                li(a_href(_('Exporting'), 'exporting')))),
        li(
            a_href(_('E-mail (Outlook &amp; Thunderbird) integration'), 'email'),
            ul(
                li(a_href(_('About e-mail integration'), 'aboutemail')),
                li(a_href(_('Attaching an e-mail to a task'), 'emailattach')),
                li(a_href(_('Creating a task from an e-mail'), 'emailcreate')))),
        li(
            a_href(_('SyncML support'), 'syncml'),
            ul(
                li(a_href(_('What is SyncML'), 'aboutsyncml')),
                li(a_href(_('Setup'), 'syncmlsetup')),
                li(a_href(_('Limitations'), 'syncmllimits')),
                li(a_href(_('Troubleshooting'), 'syncmltrouble')),
                li(a_href(_('Purging deleted items'), 'syncmlpurge')))),
        li(
            a_href(_('iPhone and iPod Touch'), 'iphone'),
            ul(
                li(a_href(_('Task Coach on the iPhone'), 'taskcoachiphone')),
                li(a_href(_('Configuration'), 'iphoneconf')),
                li(a_href(_('Troubleshooting'), 'iphonetrouble')))),
        li(
            a_href(_('Task templates'), 'templates'),
            ul(
                li(a_href(_('About templates'), 'abouttemplates')),
                li(a_href(_('Using templates'), 'usingtemplates'))))))
  

_taskSection = sequence(
    h3(
        a_name(_('Tasks'), 'tasks')),
    h4(
        a_name(_('About tasks'), 'abouttasks')),
    p(
        _('''Tasks are the basic objects that you manipulate. Tasks can
represent anything from a single little thing you have to do to a complete 
project consisting of different phases and numerous activities.''')),
    h4(
        a_name(_('Task properties'), 'taskproperties')),
    p(
        _('Tasks have the following properties you can change:'),
        ul(
            li(_('Subject: a single line that summarizes the task.')),
            li(_('Description: a multi-line description of the task.')),
            li(_('''Due date: the date the task should be finished. 
This can be 'None' indicating that this task has no fixed due date.''')),
            li(_('''Start date: the first date on which the task can be started. 
The start date defaults to the date the task is created. It can also be 'None' 
indicating that you don't really want to start this task. This can be convenient 
for e.g. registering sick leave.''')),
            li(_('''Completion date: this date is 'None' as long as the task has 
not been completed. It is set to the current date when you mark the task as 
completed. The completion date can also be entered manually.''')),
            li(_('''Prerequisites: other tasks that need to be completed before
a task can be started. The task is inactive until the last prerequisite task is 
completed. Note that if the task has a specific start date set, that start
date has to be in the past <em>and</em> all prerequisite tasks need to be
completed before the task becomes active.''')),
            li(_('Budget: amount of hours available for the task.')),
            li(_('Hourly fee: the amount of money earned with the task per hour.')),
            li(_('''Fixed fee: the amount of money earned with the task 
regardless of the time spent.''')))),
    p(
        _('The following properties are calculated from the properties above:'),
        ul(
            li(_('Days left: the number of days left until the due date.')),
            li(_('''Dependencies: other tasks that can be started when the 
prerequisite task has been completed.''')),
            li(_('Time spent: effort spent on the task.')),
            li(_('Budget left: task budget minus time spent on the task.')),
            li(_('Revenue: hourly fee times hours spent plus fixed fee.')))),
    h4(
        a_name(_('Task states'), 'taskstates')),
    p(
        _('Tasks always have exactly one of the following states:'),
        ul(
            li(_('Active: the start date is in the past and the due date in the future;')),
            li(_('''Inactive: the start date is in the future, and/or not all 
prerequisite tasks have been completed;''')),
            li(_('Completed: the task has been completed.')))),
    p(
        _('In addition, tasks can be referenced as:'),
        ul(
            li(_('Over due: the due date is in the past;')),
            li(_('''Due soon: the due date is soon (what 'soon' is, can be 
changed in the preferences);''')),
            li(_('Over budget: no budget left;')),
            li(_('Under budget: still budget left;')),
            li(_('No budget: the task has no budget.')))),
    h4(
        a_name(_('Task colors'), 'taskcolors')),
    p(
        _('The text of tasks is colored according to the following rules:'),
        ul(
            li(_('Over due tasks are red;')),
            li(_('Tasks due soon are orange;')),
            li(_('Active tasks are black text with a blue icon;')),
            li(_('Future tasks are gray, and')),
            li(_('Completed tasks are green.'))),   
        _('''This all assumes you have not changed the text colors through the 
preferences dialog, of course.''')),
    p(
        _('''The background color of tasks is determined by the categories the 
task belongs to. See the section about 
<a href="#categoryproperties">category properties</a> below.''')))

_effortSection = sequence(
    h3(
        a_name(_('Effort'), 'effort')),
    h4(
        a_name(_('About effort'), 'abouteffort')),
    p(
        _('''Whenever you spent time on tasks, you can record the amount of time
spent by tracking effort. Select a task and invoke 'Start tracking effort' in
the Effort menu or context menu or via the 'Start tracking effort' toolbar 
button.''')),
    h4(
        a_name(_('Effort properties'), 'effortproperties')),
    p(
        _('Effort records have the following properties you can change:'),
        ul(
            li(_('Task: the task the effort belongs to.')),
            li(_('Start date/time: start date and time of the effort.')),
            li(_('''Stop date/time: stop date and time of the effort. This can be 
'None' as long as you are still working on the task.''')),
            li(_('Description: a multi-line description of the effort.')))),
    p(
        _('The following properties are calculated from the properties above:'),
        ul(
            li(_('Time spent: how much time you have spent working on the task.')),
            li(_('Revenue: money earned with the time spent.')))))   

_categorySection = sequence(
    h3(
        a_name(_('Categories'), 'categories')),
    h4(
        a_name(_('About categories'), 'aboutcategories')),
    p(
        _('''Tasks and notes may belong to one or more categories. First, you 
need to create the category that you want to use via the 'Category' menu. Then, 
you can add items to one or more categories by editing the item and checking the 
relevant categories for that item in the category pane of the edit dialog.''')),
    p(
        _('''You can limit the items shown in the task and notes viewers to one 
or more categories by checking a category in the category viewer. For example, 
if you have a category 'phone calls' and you check that category, the task 
viewers will only show tasks belonging to that category; in other words the 
phone calls you need to make.''')),
    h4(
        a_name(_('Category properties'), 'categoryproperties')),
    p(
        _('Categories have the following properties you can change:'),
        ul(
            li(_('Subject: a single line that summarizes the category.')),
            li(_('Description: a multi-line description of the category.')),
            li(_('''Mutually exclusive subcategories: a check box indicating
whether the subcategories of the category are mutual exclusive. If they are,
items can only belong to one of the subcategories. When filtering, you can only
filter by one of the subcategories at a time.''')),
            li(_('''Appearance properties such as icon, font and colors: 
the appearance properties are used to render the category, but also the items
that belong to that category. If a category has no color, font or icon of its 
own, but it has a parent category with such a property, the parent's property 
will be used. If an item belongs to multiple categories that each have a color 
associated with it, a mixture of those colors will be used to render that 
item.''')))))

_noteSection = sequence(
    h3(
        a_name(_('Notes'), 'notes')),
    h4(
        a_name(_('About notes'), 'aboutnotes')),
    p(
        _('''Notes can be used to capture random information that you want
to keep in your task file. Notes can be stand-alone or be part of other items,
such as tasks and categories. Stand-alone notes are displayed in the notes
viewer. Notes that are part of other items are not displayed in the notes
viewer.''')),
    h4(
        a_name(_('Note properties'), 'noteproperties')),
    p(
        _('Notes have the following properties you can change:'),
        ul(
            li(_('Subject: a single line that summarizes the note.')),
            li(_('Description: a multi-line description of the note.')),
            li(_('Appearance properties such as icon, font and colors.')))))


_printingAndExportingSection = sequence(
    h3(
        a_name(_('Printing and exporting'), 'printingandexporting')),
    h4(
        a_name(_('About printing and exporting'), 'aboutprintingandexporting')),
    p(
        _('''Both printing and exporting work in the same way: when you print
or export data, the data from the active viewer is printed or exported.
Moreover, the data is printed or exported in the same way as the viewer is 
displaying it. The data is printed or exported in the same order as the
viewer is displaying it. The columns that are visible determine what 
details get printed or exported. When you filter items, for example hide
completed tasks, those items don't get printed or exported.''')),
    h4(
        a_name(_('Printing'), 'printing')),
    p(
        _('''Prepare the contents of a viewer, by putting the items in the 
right order, show or hide the appropriate columns and apply the relevant 
filters.''')),
    p(
        _('''You can preview how the print will look
using the File -> Print preview menu item. You can edit the page settings
using File -> Page setup. When printing and the platform supports it, you can 
choose to print all visible items in the active viewer, or just the 
selected items.''')),
    h4(
        a_name(_('Exporting'), 'exporting')),
    p(
        _('''Prepare the contents of a viewer, by putting the items in the 
right order, show or hide the appropriate columns and apply the relevant 
filters.''')),
    p(
        _('''Next, choose the format you want to export to and whether you
want to export all visible items or just the selected ones. Available formats
to export to include CSV (comma separated format), HTML and iCalendar. When
you export to HTML, a CSS file is created that you can edit to change
the appearance of the HTML.''')))


_emailSection = sequence(
    h3(
        a_name(_('E-mail (Outlook &amp; Thunderbird) integration'), 'email')),
    h4(
        a_name(_('About e-mail integration'), 'aboutemail')),
    p(
        _('''%(name)s integrates with both Outlook and Thunderbird mail user
agents, through drag and drop. This has some limitations; e-mails are
copied in a directory next to the %(name)s file, as .eml files and are
later opened using whatever program is associated with this file type
on your system. On the other hand, this allows you to open these
e-mail attachments on a system which is different from the one you
created it first.''')%meta.metaDict),
    p(
        _('''Due to a Thunderbird limitation, you can't drag and drop several
e-mails from Thunderbird. This does not apply to Outlook.''')),
    h4(
        a_name(_('Attaching an e-mail to a task'), 'emailattach')),
    p(
        _('''There are two ways to attach an e-mail to a task; you can:'''),
        ul(
            li(_('Drop it on a task either in the task tree or the task list.')),
            li(_('Drop it in the attachment pane in the task editor.')))),
    h4(
        a_name(_('Creating a task from an e-mail'), 'emailcreate')),
    p(
        _('''Dropping an e-mail on an empty part of the task tree or task list
creates a new task. Its subject is the subject of the mail, its
description is its content. Additionally, the mail is automatically
attached to the newly created task.''')))


_syncmlSection = sequence(
    h3(
        a_name(_('SyncML support'), 'syncml')),
    h4(    
        a_name(_('What is SyncML'), 'aboutsyncml')),
    p(
        _('''SyncML is an XML protocol designed to synchronize several
applications with a server. A popular open-source server is <a
href="http://www.funambol.com/" target="_blank">Funambol</a>. Synchronization 
clients are available for many devices and applications (Outlook, Pocket PC,
iPod, iPhone, Evolution, etc...), as well as so-called "connectors"
which allow the server to synchronize with Exchange, Google Calendar,
etc.''')),
    p(
        _('''%(name)s has built-in SyncML client support. This means you can
setup %(name)s to synchronize with the same SyncML server you
synchronize Outlook with and have all Outlook tasks and notes in
your %(name)s file, as well as %(name)s tasks and notes in Outlook. Or
your Pocket PC.''')%meta.metaDict),
    h4(
        a_name(_('Setup'), 'syncmlsetup')),
    p(
        _('''This feature is optional and off by default. In order to turn it on,
go to the preferences dialog and check it on the Features page.''')),
    p(
        _('''To setup SyncML, edit the SyncML preferences in Edit/SyncML 
preferences. Fill in the synchronization URL, your ID on the server and choose 
which items to synchronize (tasks and/or notes). The URL depends on the server
you choose; some examples are:'''),
        ul(
            li('''<a href="http://www.scheduleworld.com/" target="_blank">ScheduleWorld</a>:
http://sync.scheduleworld.com/funambol/ds'''),
            li('''<a href="http://memotoo.com" target="_blank">MemoToo</a>:
http://sync.memotoo.com/syncml''')),
        _('''The database names are pretty standard; the default values 
should work.''')),
    p(
        _('''Each task file has its own client ID, so that two different task 
files will be considered different "devices" by the server.''')),
    h4(
        a_name(_('Limitations'), 'syncmllimits')),
    p(
        _('''Some limitations are due to the fact that, the underlying data 
type being vcalendar, some %(name)s features cannot be presented to the 
server.''')%meta.metaDict,
        ul(
            li(_('Task and category hierarchy are lost to the server.')),
            li(_('Recurrence and reminders are not supported yet.')),
            li(_('Note categories are lost to the server.')),
            li(_('''The conflict detection/resolution system is a work around a 
Funambol limitation. It should work in most cases, but if many applications
synchronize with the same server at the same time, problems may rise.''')),
            li(_('Probably some others...')))),
    h4(
        a_name(_('Troubleshooting'), 'syncmltrouble')),
    p(
        _('''The SyncML menu items are only present if your platform is 
supported. Currently supported platforms are:'''),
        ul(
            li(_('Windows, 32 bits (see below)')),
            li(_('Linux, 32 bits')),
            li(_('Mac OS 10.3 and later, both Intel and PPC'))),
        _('''You may experience problems under Windows if you don't have the 
Microsoft Visual 8 runtime installed. You can download it on the
<a target="_blank" href="%s"> Microsoft download site</a>.''')% _MSURL),
    h4(
        a_name(_('Purging deleted items'), 'syncmlpurge')),
    p(
        _('''When SyncML is enabled, deleting a task or a note does not actually
delete it, but rather mark it as deleted. The deleted task or note is actually 
removed from the task or note list on the next synchronization. For this reason, 
if you happen to use the SyncML feature, then disable it without having done a 
sync, there may be some deleted notes or tasks in your task file. This is not a 
problem, but takes a little more disk space.''')),
    p(
        _('''In this case, the "Purge deleted items" menu item in the File menu 
can be used to actually delete these tasks. It is only enabled when you
need it, that is when there are items to purge. Be aware that after doing this,
if you re-enable SyncML and make a sync with the same server you used
previously, all those items will reappear, as the server
doesn't know they're deleted.''')))


_iPhoneSection = sequence(
    h3(
        a_name(_('iPhone, iPod Touch and iPad'), 'iphone')),
    h4(
        a_name(_('%(name)s on the iPhone/iPod Touch/iPad')%meta.metaDict, 'taskcoachiphone')),
    p(
        _('''There is an iPhone/iPod Touch/iPad companion app for %(name)s, 
available on <a 
href="http://itunes.apple.com/WebObjects/MZStore.woa/wa/viewSoftware?id=311403563&mt=8"
target="_blank">Apple's AppStore</a>. (If you don't have iTunes installed on 
your computer, you'll be presented a page where you can download iTunes). 
It supports the following features:''')%meta.metaDict,
        ul(
            li(_('''Basic task attributes: subject, description, dates (with 
recurrence)...''')),
            li(_('Hierarchical tasks and categories')),
            li(_('Time tracking')),
            li(_('Multiple task files')),
            li(_('Two-way synchronization with %(name)s on the desktop')%meta.metaDict)),
    p(
        _('''The application is universal and has a custom iPad UI.''')),
    h4(
        a_name(_('Configuration'), 'iphoneconf')),
    h5(
        _('Configuration on the iPhone/iPod Touch/iPad')),
    p(
        _('''There are some settings for the iPhone/iPod Touch/iPad app in the 
Settings application:'''),
        ul(
            li(_('Show completed: whether to show completed tasks.')),
            li(_('''Show inactive: whether to show inactive tasks (start date 
in the future).''')),
            li(_('''Icon position: the LED icon may show up either on the 
left side or the right side of the screen.''')),
            li(_('''Compact mode: if this is enabled, the task list has smaller 
LEDs and doesn't show categories or dates.''')),
            li(_('''Confirm complete: if enabled, a message box will pop up for 
confirmation when you mark a task complete by tapping its LED.''')),
            li(_('''# days due soon: How many days in the future is 
considered "soon".''')))),
    h5(
        _('Configuration on the desktop, all platforms')),
    p(
        _('''Before synchronizing, you must also configure %(name)s on the 
desktop; in the preferences, in the "Features" tab, check "Enable iPhone
synchronization". Restart %(name)s. Now, in the preferences, choose the 
"iPhone" tab and fill in at least the password.''')%meta.metaDict),
    p(
        _('''When you tap the "Sync" button in the category view, %(name)s
will automatically detect running instances of %(name)s on your
desktop and ask you to select one (you may have several instances
running on different computers on your network, or several instances
on the same computer). The name displayed is, by default, some string
identifying the computer it's running on. To customize this, you may
change the "Bonjour service name" in the configuration.''')%meta.metaDict),
    p(
        _('''%(name)s will remember the chosen instance and try it next time
you synchronize; if it's not running, it will prompt you again.''')%meta.metaDict),
    p(
        _('''Note that this synchronization happens through the network; there 
is no need for the device to be connected through USB nor for iTunes to
be running.''')),
    h5(
        _('Configuration on Windows')),
    p(
        _('''On Windows, you must install <a
href="http://support.apple.com/kb/dl999">Bonjour for Windows</a> and
unblock it when asked by the firewall.''')),
    h5(
        _('Configuration on Linux')),
    p(
        _('''On Linux, you must have the <a href="http://avahi.org/">Avahi</a> 
daemon installed and running. Most modern distributions already have it. You 
must also install the dnscompat package; its name depends on your distribution 
(libavahi-compat-libdnssd1 on Ubuntu for instance).''')),
    h4(
        a_name(_('Troubleshooting'), 'iphonetrouble')),
    h5(
        _('''I can't seem to find the iPhone/iPod Touch app on Apple's 
website''')),
    p(
        _('''You need to have iTunes installed on your computer to browse 
Apple's App Store. <a href="http://www.apple.com/itunes/" target="_blank">Get 
iTunes</a>.''')),
    h5(
        _('''My computer doesn't appear in the list when trying to sync''')),
    p(
        _('''Check that your iPhone/iPod Touch is connected to the same network 
your computer is through WiFi.''')),
    h5(
        _("The iPhone can't connect to my computer")),
    p(
        _('If you have a firewall, check that ports 4096-4100 are open.'))))


_templatesSection = sequence(
    h3(
        a_name(_('Task templates'), 'templates')),
    h4(
        a_name(_('About templates'), 'abouttemplates')),
    p(
        _('''Templates are blueprints for new tasks. Right now, the only task 
properties that can be "parameterized" are the dates. When instantiating a 
template, the created task has its dates replaced with dates relative to the 
current date.''')),
    h4(
        a_name(_('Using templates'), 'usingtemplates')),
    p(
        _('''One can create a template by selecting a task (only one) and click 
on the "Save task as template" item in the File menu. All subtasks, notes and 
attachments are part of the template. Only categories are not saved.''')),
    p(
        _('''You can also create a new template from a pre-made template file 
(.tsktmpl); just select "Add template" in the File menu and select the file. 
Template files are stored in a subdirectory of the directory where TaskCoach.ini 
is.''')),
    p(
        _('''In order to instantiate a task template, use the "New task from 
template" menu in the Task menu, or the equivalent toolbar button. When the 
task is created, the due, start and completion dates, if applicable, are 
reevaluated relatively to the current date. That means that if you create a 
template from a task starting today and due tomorrow, every time the template 
is instantiated, the start date will be replaced by the current date and the 
due date by the current date plus one day.''')))


helpHTML = _TOC + _taskSection + _effortSection + _categorySection + \
    _printingAndExportingSection + _emailSection + _syncmlSection + \
    _iPhoneSection + _templatesSection


aboutHTML = _('''<h4>%(name)s - %(description)s</h4>
<h5>Version %(version)s, Revision %(revision)s, %(date)s</h5>
<p>By %(author)s &lt;%(author_email)s&gt;<p>
<p><a href="%(url)s" target="_blank">%(url)s</a></p>
<p>%(copyright)s</p>
<p>%(license_notice_html)s</p>
''')%meta.metaDict

doubleline = '================================================================\n'

header = doubleline + '%(name)s - %(description)s\n'%meta.metaDict + doubleline

aboutText = header + _('''
Version %(version)s, Revision %(revision)s, %(date)s

By %(author)s <%(author_email)s>

%(url)s

%(copyright)s
%(license)s

''')%meta.metaDict + doubleline

installText = header + '''

--- Prerequisites ----------------------------------------------

You need Python version %(pythonversion)s or higher and wxPython 
version %(wxpythonversion)s or higher.


--- Testing ----------------------------------------------------

Before installing, you may want to run the unittests included.
Issue the following command:

  cd tests; python test.py

If all goes well, you should see a number of dots appearing and
the message 'Ran X tests in Y seconds. OK'. If not, you'll get
one or more failed tests. In that case, please run the tests
again, redirecting the output to a textfile, like this:

  python test.py 2> errors.txt

Please mail me the errors.txt file and your platform information
(operating system version, Python version and wxPython version).


--- Installation -----------------------------------------------

There are two options to install %(name)s: 

First, you can simply move this directory to some suitable 
location and run taskcoach.py (or taskcoach.pyw if you are on 
the Windows platform) from there.

Alternatively, you can use the Python distutils setup script
to let Python install %(name)s for you. In that case run the
following command:

  python setup.py install

If you have a previous version of %(name)s installed, you may
need to force old files to be overwritten, like this:

  python setup.py install --force

'''%meta.metaDict + doubleline

buildText = header + '''

--- Building ---------------------------------------------------

To be done.

'''%meta.metaDict + doubleline
