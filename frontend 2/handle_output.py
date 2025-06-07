import os
from PyQt5.QtMultimedia import QMediaContent
from PyQt5.QtCore import QUrl


def get_output():
    with open('frontend/output1.txt', 'r') as f:
            text = f.read()
            text = text.split(" ")
            to_set = ""
            for t in text:
                if 'DOCTOR:' in t:
                    preword = ""
                    if '\n' in t:
                        splitted = t.split('\n')
                        preword = splitted[0]
                        to_insert = splitted[1]
                        to_set += preword + """ <br><span style="color : green; font-weight: bold;">"""+to_insert+"""</span> """
                    else:
                        to_insert = t
                        to_set += """<span style="color : green; font-weight: bold;">"""+to_insert+"""</span> """
                elif "PATIENT:" in t:
                    preword = ""
                    if '\n' in t:
                        splitted = t.split('\n')
                        preword = splitted[0]
                        to_insert = splitted[1]
                        to_set += preword + """ <br><span style="color : red; font-weight: bold;">"""+to_insert+"""</span> """
                    else:
                        to_insert = t
                        to_set += """<span style="color : red; font-weight: bold;">"""+to_insert+"""</span> """
                else:
                    to_set += t + " "
    video_path = os.path.abspath("frontend/video.mp4")
    if os.path.exists(video_path):
        video = QMediaContent(QUrl.fromLocalFile(video_path))
    else:
        video = "Video non trovato!"

    return [video, to_set, None]