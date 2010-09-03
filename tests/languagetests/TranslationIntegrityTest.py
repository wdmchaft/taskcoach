# -*- coding: UTF-8 -*-

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

import string, re # pylint: disable-msg=W0402
import test
from taskcoachlib import meta


class TranslationIntegrityTestsMixin(object):
    ''' Unittests for translations. This class is subclassed below for each
        translated string in each language. '''
        
    def testMatchingNonLiterals(self):
        for symbol in '\t', '|', '%s', '%d', '%.2f', '%(name)s', '%(version)s',\
            '%(filename)s', '%(nrtasks)d', '%(url)s', '%(description)s',\
            '%(copyright)s', '%(author)s', '%(author_email)s', '%(license)s',\
            '%(date)s':
            self.assertEqual(self.englishString.count(symbol), 
                self.translatedString.count(symbol),
                "Symbol ('%s') doesn't match for '%s' and '%s'"%(symbol,
                    self.englishString, self.translatedString))
            
    def testMatchingAmpersands(self):
        # If the original string contains zero or one ampersands, it may be 
        # an accelerator. In that case, we don't require the translated string
        # to have an accelerator as well, because many translators don't use 
        # it and it doesn't break the application. However, if the original
        # string contains more than one ampersand it's probably HTML. In that
        # case we do require the number of ampersands to match exactly in the 
        # original and translated string.
        translatedString = self.removeUmlauts(self.translatedString)
        nrEnglishAmpersand = self.englishString.count('&')
        nrTranslatedAmpersand = translatedString.count('&')
        if nrEnglishAmpersand <= 1 and not '\n' in self.englishString:
            self.failUnless(nrTranslatedAmpersand in [0,1], 
                "'%s' has more than one '&'"%self.translatedString)
        else:
            self.assertEqual(nrEnglishAmpersand, nrTranslatedAmpersand,
                "'%s' has more or less '&'s than '%s'"%(self.translatedString,
                self.englishString))

    def testMatchingShortCut(self):
        for shortcutPrefix in ('Ctrl+', 'Shift+', 'Alt+',
                               'Shift+Ctrl+', 'Shift+Alt+'):
            self.assertEqual(self.englishString.count('\t'+shortcutPrefix),
                             self.translatedString.count('\t'+shortcutPrefix),
                             "Shortcut prefix ('%s') doesn't match for '%s' and '%s'"%(shortcutPrefix,
                                 self.englishString, self.translatedString))
    
    @staticmethod
    def ellipsisCount(text):
        return text.count('...') + text.count('…')
    
    def testMatchingEllipses(self):
        self.assertEqual(self.ellipsisCount(self.englishString),
                         self.ellipsisCount(self.translatedString),
                         "Ellipses ('...') don't match for '%s' and '%s'"%(self.englishString, self.translatedString))

    umlautRE = re.compile(r'&[A-Za-z]uml;')
    @classmethod
    def removeUmlauts(cls, text):
        return re.sub(cls.umlautRE, '', text)      
    

def installAllTestCaseClasses():
    for language in getLanguages():
        installTestCaseClasses(language)

def getLanguages():
    return [language for language in meta.data.languages.values() \
            if language is not None]

def installTestCaseClasses(language):
    translation = __import__('taskcoachlib.i18n.%s'%language, fromlist=['dict'])
    for englishString, translatedString in translation.dict.iteritems():        
        installTranslationTestCaseClass(language, englishString, 
                                              translatedString)

def installTranslationTestCaseClass(language, englishString, 
                                          translatedString):
    testCaseClassName = translationTestCaseClassName(language, englishString)
    testCaseClass = translationTestCaseClass(testCaseClassName, 
        language, englishString, translatedString)
    globals()[testCaseClassName] = testCaseClass

def translationTestCaseClassName(language, englishString, 
                                 prefix='TranslationIntegrityTest'):
    ''' Generate a class name for the test case class based on the language
        and the English string. '''
    # Make sure we only use characters allowed in Python identifiers:
    englishString = englishString.replace(' ', '_')
    allowableCharacters = string.ascii_letters + string.digits + '_'
    englishString = ''.join([char for char in englishString \
                             if char in allowableCharacters])
    className = '%s_%s_%s'%(prefix, language, englishString)
    count = 0
    while className in globals(): # Make sure className is unique
        count += 1
        className = '%s_%s_%s_%d'%(prefix, language, englishString, count)
    return className

def translationTestCaseClass(className, language, englishString, translatedString):
    class_ = type(className, (TranslationIntegrityTestsMixin, test.TestCase), {})
    class_.language = language
    class_.englishString = englishString
    class_.translatedString = translatedString
    return class_


# Create all test cases and install them in the global name space:
installAllTestCaseClasses() 
