import boto3
import random


class VoicePicker(object):
    def __init__(self, **kwargs):
        self.include_voices = kwargs.get('include_voices')
        self.exclude_voices = kwargs.get('exclude_voices')
        self.include_languages = kwargs.get('include_languages')
        self.polly = boto3.client("polly")

    def get_voices(self):
        self.voices = []
        if (self.include_languages):
            langs = [l.strip() for l in self.include_languages.split(',')]
            for l in langs:
                resp = self.polly.describe_voices(LanguageCode=l)
                for v in resp["Voices"]:
                    self.voices.append(v["Name"])
        else:
            resp = self.polly.describe_voices()
            for v in resp["Voices"]:
                self.voices.append(v["Name"])
        if (self.include_voices):
            i = [v.strip() for v in self.include_voices.split(',')]
            for v in self.voices[:]:
                if v not in i:
                    self.voices.remove(v)

        if (self.exclude_voices):
            e = [v.strip() for v in self.exclude_voices.split(',')]
            for v in self.voices[:]:
                if v in e:
                    self.voices.remove(v)

    def pick_a_voice(self, **kwargs):
        exclude = kwargs.get('Exclude')
        voice = random.choice(self.voices)
        while voice == exclude:
            voice = random.choice(self.voices)
        return voice
