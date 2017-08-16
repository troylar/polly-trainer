import click
from polly import VoicePicker
from parser import Parser
from export import Exporter


@click.command()
@click.option('--include_languages', help='Language to randomly select ' +
                                          'voice from')
@click.option('--exclude_voices', help='Comma-delimited voices to exclude ' +
                                       'from the random choice')
@click.option('--include_voices', help='Only use this comma-delimited ' +
                                       'list of voices')
@click.option('--genre', help='Genre MP3 tag')
@click.option('--album', help='Album MP3 tag')
@click.option('--artist', help='Artist MP3 tag')
@click.option('--filename', help='File to import')
@click.option('--output_folder', help='Output folder')
@click.option('--overwrite/--do-not-overwrite', default=True)
def main(exclude_voices, include_voices, genre, album, artist,
         filename, include_languages, output_folder, overwrite):
    vp = VoicePicker(include_voices=include_voices,
                     exclude_voices=exclude_voices,
                     include_languages=include_languages)
    vp.get_voices()
    p = Parser(filename=filename)
    p.read_file()
    e = Exporter(VoicePicker=vp, QAndA=p.q_and_a, OutputFolder=output_folder)
    e.export_files(Genre=genre, Artist=artist, Album=album,
                   Overwrite=overwrite)


if __name__ == '__main__':
    main()
