# -*- coding: utf-8 -*-

import gettext
import locale
import os
import sys
import ast
import classes.xml_conn

from classes.extras import reverse
from classes.extras import unival


class Language:
    def __init__(self, configo, path):
        self.locale_dir = unival(os.path.join(path, 'locale/'))
        if not os.path.isdir(self.locale_dir):
            self.locale_dir = "/usr/share/locale/"
        if 'LC_MESSAGES' in vars(locale):
            # linux
            locale.setlocale(locale.LC_MESSAGES, '')
        else:
            # windows
            locale.setlocale(locale.LC_ALL, '')

        self.config = configo
        self.alphabet_26 = ["en_GB", "en_US", "pt_PT"]
        self.def_imported = False
        self.trans = dict()
        self.lang_titles = self.config.lang_titles
        self.all_lng = self.config.all_lng
        self.ok_lng = self.config.ok_lng
        self.tts_disabled_lngs = []  # will be overridden with data from xml
        self.xml_langs = classes.xml_conn.XMLLangs()

    def load_language(self, lang_code=None):
        if lang_code is None:
            if self.config.settings["lang"] not in self.all_lng:
                self.config.reset_settings()

            self.lang = self.config.settings["lang"]
        else:
            if lang_code not in self.all_lng:
                self.lang = 'en_GB'
            else:
                self.lang = lang_code

        self.get_lang_attr()

    def _n(self, word, count):
        return self.trans[self.lang].ngettext(word, word, count)

    def get_lang_attr(self):
        filename = os.path.join(self.locale_dir, self.lang, "LC_MESSAGES", "eduactiv8.mo")
        try:
            self.trans[self.lang] = gettext.GNUTranslations(open(filename, "rb"))
        except IOError:
            print("Locale not found. Using default messages")
            self.trans[self.lang] = gettext.NullTranslations()

        self.trans[self.lang].install()

        import i18n.custom.default
        self.oi18n = i18n.custom.default.I18n()
        self.kbrd = None
        self.ltr_text = True
        self.ltr_numbers = True
        self.ltr_math = True
        self.has_uc = True
        self.has_cursive = True
        font_variant = 0
        self.ico_suffix = ""
        self.lang_id = 0  # used to identify the language in database - do not reorganize numbers when adding new language

        lang = self.xml_langs.get_lang_config(self.lang)
        self.tts_disabled_lngs = self.xml_langs.get_tts_disabled()
        if lang is not None:
            if lang.attrib['voice_mb'] != "None" and lang.attrib['use_mb'] == "True":
                self.voice = eval(lang.attrib["voice_mb"])
            elif lang.attrib['voice'] != "None":
                self.voice = eval(lang.attrib["voice"])
            else:
                self.voice = None

            code_lc = self.lang.lower()
            exec("import i18n.custom." + code_lc)
            exec("import i18n.custom.word_lists." + code_lc + "_di")
            exec("import i18n.custom.a4a_py." + self.lang + " as a4a_word_lst")
            if ast.literal_eval(lang.attrib['has_keyboard']) is True:
                exec("import i18n.custom.kbrd." + code_lc)
                exec("import i18n.custom.kbrd." + code_lc[0:2] + "_course")
                self.kbrd = eval("i18n.custom.kbrd." + code_lc)
                self.kbrd_course_mod = eval("i18n.custom.kbrd." + code_lc[0:2] + "_course")

            self.di = eval("i18n.custom.word_lists." + code_lc + "_di.di")
            self.lang_file = eval("i18n.custom." + code_lc)
            self.lang_id = int(lang.attrib["id"])

            self.ltr_text = ast.literal_eval(lang.attrib['ltr'])
            self.has_uc = ast.literal_eval(lang.attrib['has_uc'])
            self.has_cursive = ast.literal_eval(lang.attrib['has_cursive'])
            self.ico_suffix = lang.attrib['ico_suffix']
        else:
            print("Language file not found.")
            import i18n.custom.en_gb
            import i18n.custom.word_lists.en_gb_di
            import i18n.custom.kbrd.en_gb
            import i18n.custom.kbrd.en_course
            import i18n.custom.a4a_py.en_GB as a4a_word_lst
            self.voice = ["-ven+m1"]
            self.di = i18n.custom.word_lists.en_gb_di.di
            self.lang_file = i18n.custom.en_gb
            self.kbrd = i18n.custom.kbrd.en_gb
            self.kbrd_course_mod = i18n.custom.kbrd.en_course
            self.lang_id = 1

        if self.lang == 'sr':
            self.time2str_short = self.lang_file.time2str_short
        elif self.lang == 'ru':
            self.time2spk_short = self.lang_file.time2spk_short
            self.time2str_short = self.lang_file.time2str_short
            self.time2spk = self.lang_file.time2spk
        elif self.lang == 'he':
            self.time2spk = self.lang_file.time2spk
            self.alpha = i18n.custom.he.alpha
            self.n2spk = self.lang_file.n2spk
        elif self.lang == 'ar':
            self.alpha = None
            self.n2spk = self.lang_file.n2spk

        if self.lang in ["ar", "he"]:
            self.config.font_multiplier = 1.1
            self.config.font_line_height_adjustment = 1.5
            self.config.font_start_at_adjustment = 5
        else:
            self.config.font_multiplier = 1
            self.config.font_line_height_adjustment = 1
            self.config.font_start_at_adjustment = 0

        if self.kbrd is None:
            import i18n.custom.kbrd.en_gb
            import i18n.custom.kbrd.en_course
            self.kbrd = i18n.custom.kbrd.en_gb
            self.kbrd_course_mod = i18n.custom.kbrd.en_course

        self.d = dict()
        self.b = dict()
        self.dp = dict()
        self.kbrd_course = self.kbrd_course_mod.course

        self.d.update(self.oi18n.d)
        self.d.update(self.lang_file.d)
        self.b.update(self.oi18n.b)
        self.numbers = self.lang_file.numbers
        self.numbers2090 = self.lang_file.numbers2090
        self.n2txt = self.lang_file.n2txt
        self.time2str = self.lang_file.time2str
        self.fract2str = self.lang_file.fract2str

        self.solid_names = self.oi18n.solid_names
        self.shape_names = self.oi18n.shape_names
        self.letter_names = self.lang_file.letter_names
        self.config.set_font_family(font_variant)
        if not self.ltr_text:
            for each_d in [self.d, self.b]:
                for key in each_d.keys():
                    if isinstance(each_d[key], list):
                        for index in range(len(each_d[key])):
                            if sys.version_info < (3, 0):
                                if isinstance(each_d[key][index], basestring):
                                    each_d[key][index] = reverse(each_d[key][index], self.alpha, self.lang)
                            else:
                                if isinstance(each_d[key][index], str):
                                    each_d[key][index] = reverse(each_d[key][index], self.alpha, self.lang)
                    else:
                        each_d[key] = reverse(each_d[key], self.alpha, self.lang)
            for each in [self.solid_names, self.shape_names]:
                for index in range(len(each)):
                    if sys.version_info < (3, 0):
                        if isinstance(each[index], basestring):
                            each[index] = reverse(each[index], self.alpha, self.lang)
                    else:
                        if isinstance(each[index], str):
                            each[index] = reverse(each[index], self.alpha, self.lang)

        self.dp.update(self.d)
        self.dp.update(self.lang_file.dp)
        if self.lang == "he":
            s = unival(self.d['abc_flashcards_word_sequence'][0])
            if len(s) > 0:
                if s[0] == unival("א"):
                    self.d['abc_flashcards_word_sequence'] = self.d['abc_flashcards_word_sequencer']

        self.alphabet_lc = self.lang_file.alphabet_lc
        self.alphabet_uc = self.lang_file.alphabet_uc
        self.accents_lc = self.lang_file.accents_lc
        self.accents_uc = self.lang_file.accents_uc

        self.d["a4a_animals"] = a4a_word_lst.d["a4a_animals"]
        self.d["a4a_sport"] = a4a_word_lst.d["a4a_sport"]
        self.d["a4a_body"] = a4a_word_lst.d["a4a_body"]
        self.d["a4a_people"] = a4a_word_lst.d["a4a_people"]
        self.d["a4a_food"] = a4a_word_lst.d["a4a_food"]
        self.d["a4a_clothes_n_accessories"] = a4a_word_lst.d["a4a_clothes_n_accessories"]
        self.d["a4a_actions"] = a4a_word_lst.d["a4a_actions"]
        self.d["a4a_construction"] = a4a_word_lst.d["a4a_construction"]
        self.d["a4a_nature"] = a4a_word_lst.d["a4a_nature"]
        self.d["a4a_jobs"] = a4a_word_lst.d["a4a_jobs"]
        self.d["a4a_fruit_n_veg"] = a4a_word_lst.d["a4a_fruit_n_veg"]
        self.d["a4a_transport"] = a4a_word_lst.d["a4a_transport"]
