import yaml
from slugify import slugify


class QAndA(object):
    def __init__(self):
        self.a_voice = ""
        self.q_voice = ""
        self.artist = ""
        self.album = ""
        self.genre = ""


class Parser(object):

    def __init__(self, **kwargs):
        self.filename = kwargs.get('filename')
        self.q_header = "QUESTION"
        self.q_and_a = []

    def read_file(self):
        with open('q.yaml', 'r') as stream:
            y = yaml.load(stream)

        n = 1
        for i in y:
            q = QAndA()
            raw_question = i['question']
            slug = slugify(raw_question)
            answer = i['answer']
            if 'genre' in i:
                q.genre = i['genre']
            if 'album' in i:
                q.genre = i['album']
            if 'artist' in i:
                q.artist = i['artist']
            if 'q_voice' in i:
                q.q_voice = i['q_voice']
            if 'a_voice' in i:
                q.a_voice = i['a_voice']
            if len(slug) > 150:
                slug = slug[:150]

            f = "{}-{}.mp3".format(str(n).zfill(3), slug)
            q.question = raw_question.strip()
            q.slug = slug
            q.filename = f
            q.answer = answer
            q.track_number = n
            self.q_and_a.append(q)
            n = n + 1
