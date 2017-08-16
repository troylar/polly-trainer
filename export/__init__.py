import boto3
import os
import tempfile
import shutil
import logging
from contextlib import closing
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
import mutagen.id3


class Exporter(object):
    def __init__(self, **kwargs):
        self.voice_picker = kwargs.get('VoicePicker')
        self.questions = kwargs.get('QAndA')
        self.output_folder = kwargs.get('OutputFolder')
        self.polly = boto3.client("polly")
        self.break_file = self.generate_break()
        self.logger = logging.getLogger(__name__)

    def export_files(self, **kwargs):
        album = kwargs.get('Album')
        artist = kwargs.get('Artist')
        genre = kwargs.get('Genre')
        overwrite = kwargs.get('Overwrite')
        output_folder = self.output_folder or './output'
        if not os.path.exists(output_folder):
            self.logger.info('Creating output folder: ' +
                             '{}'.format(output_folder))
            os.makedirs(output_folder)
        for q in self.questions:
            full_path = os.path.join(output_folder, q.filename)
            self.logger.debug('Filename: {}'.format(full_path))
            if os.path.exists(full_path) and not overwrite:
                self.logger.info('SKIPPING: File exists')
                continue
            files = []
            q_voice = q.q_voice or self.voice_picker.pick_a_voice()
            a_voice = q.a_voice or \
                self.voice_picker.pick_a_voice(Exclude=q_voice)
            self.logger.debug(' Question Voice: {}'.format(q_voice))
            self.logger.debug(' Answer Voice: {}'.format(a_voice))
            files.append(self.generate_audio(
                q_voice,
                "QUESTION. {}\n".format(q.question)))
            files.append(self.break_file)
            if len(q.answer) > 1500:
                sections = q.answer.split("\n")
                files.append(self.generate_audio(
                    a_voice,
                    "ANSWER. ".format(q.answer)))

                for s in sections:
                    if not s.strip():
                        continue
                    files.append(self.break_file)
                    files.append(self.generate_audio(
                        a_voice,
                        "{}\n".format(s)))
            else:
                files.append(self.generate_audio(
                    a_voice,
                    "ANSWER. {}\n".format(q.answer)))
            destination = open(full_path, 'wb')
            for f in files:
                shutil.copyfileobj(open(f, 'rb'), destination)
                if self.break_file == f:
                    continue
                os.remove(f)
            destination.close()

            meta = MP3(full_path, ID3=EasyID3)
            try:
                meta.add_tags(ID3=EasyID3)
            except mutagen.id3.error:
                pass
            if genre or q.genre:
                meta['genre'] = q.genre or genre
            if artist or q.artist:
                meta['artist'] = q.artist or artist
            if album or q.album:
                meta['album'] = q.album or album
            meta['title'] = q.question
            meta['tracknumber'] = str(q.track_number)
            meta.save()
            print "{} . . . Complete".format(full_path)

    def generate_break(self):
        filename = './one-second-break.mp3'
        response = self.polly.synthesize_speech(
            Text='<speak><break time="1s"/></speak>',
            OutputFormat="mp3",
            TextType="ssml",
            VoiceId=self.voice_picker.pick_a_voice())
        new_file, tmpfile = tempfile.mkstemp()
        if "AudioStream" in response:
            with closing(response["AudioStream"]) as stream:
                data = stream.read()
                fo = open(filename, "w+")
                fo.write(data)
                fo.close()
        return filename

    def generate_audio(self, voice, text):
        response = self.polly.synthesize_speech(
            Text=text,
            OutputFormat="mp3",
            VoiceId=voice)
        new_file, tmpfile = tempfile.mkstemp()
        if "AudioStream" in response:
            with closing(response["AudioStream"]) as stream:
                data = stream.read()
                fo = open(tmpfile, "w+")
                fo.write(data)
                fo.close()
        return tmpfile
