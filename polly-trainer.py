import os
import click
from polly import VoicePicker
from parser import Parser
from export import Exporter
import sys
import boto3
import json
import tempfile
import ntpath
import shutil

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
@click.option('--queue', help='Queue name to monitor')
@click.option('--bucket_name', help='Bucket name to upload ZIP files')
def main(exclude_voices, include_voices, genre, album, artist,
         filename, include_languages, output_folder, overwrite,
         queue, bucket_name):
    output_folder = output_folder or "./output"
    s3 = boto3.resource('s3')
    s3_client = boto3.client('s3')
    vp = VoicePicker(include_voices=include_voices,
                     exclude_voices=exclude_voices,
                     include_languages=include_languages)
    vp.get_voices()
    while True:
        files = []
        if (queue):
            sqs = boto3.resource('sqs')
            print 'Checking the queue . . .'
            q = sqs.get_queue_by_name(QueueName=queue)
            for msg in q.receive_messages(MessageAttributeNames=['All'],
                 WaitTimeSeconds=20):
                try:
                    m = json.loads(msg.body)
                    bucket_name = m['Records'][0]['s3']['bucket']['name']
                    key = m['Records'][0]['s3']['object']['key']
                    if key.endswith(tuple(['zip', 'err'])):
                        continue
                    file_path = '/tmp/{}'.format(key)
                    print bucket_name, key, file_path
                    s3.Bucket(bucket_name).download_file(key, file_path)
                    files.append(file_path)
                    print 'y {}'.format(len(files))
                except Exception as e:
                    print e
                finally:
                    print 'Deleting message'
                    msg.delete()
        else:
            files.append(filename)
        if len(files) == 0:
            continue

        print 'z {}'.format(len(files))
        for f in files:
            basename = ntpath.basename(f)
            try:
                p = Parser(filename=f)
                p.read_file()
                out_folder = os.path.join(output_folder, basename)
                e = Exporter(VoicePicker=vp, QAndA=p.q_and_a, OutputFolder=out_folder)
                e.export_files(Genre=genre, Artist=artist, Album=album, Overwrite=overwrite)
                new_file, tmp_file = tempfile.mkstemp()
                print tmp_file, out_folder
                shutil.make_archive(tmp_file, 'zip', out_folder)
                s3_key =  '{}.zip'.format(basename)
                s3.Bucket(bucket_name).upload_file('{}.zip'.format(tmp_file), s3_key)
            except Exception as e:
                s3_key = '{}.err'.format(basename)
                s3.Bucket(bucket_name).put_object(Body='Error Processing File:\n\n{}'.format(e),
                                                  Key=s3_key)
            finally:
                acl = s3.ObjectAcl(bucket_name, s3_key)
                response = acl.put(ACL='public-read')
        if not queue:
            break

if __name__ == '__main__':
    main()
