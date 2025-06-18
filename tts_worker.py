from fish_audio import get_voice
import uuid
import threading
import os
import shutil

def synthesis_sound(mode, save_path, context, role_id, sample_sound_path, sample_text):
    tmp_save_path = f"{save_path}/tmp_audio/tmp.mp3"
    save_path = f"{save_path}/tmp_audio/{uuid.uuid1()}.mp3"
    if mode == 0:
        get_voice(context, role_id, sample_sound_path, sample_text, tmp_save_path)
    if os.path.exists(tmp_save_path):
        if not os.path.exists(save_path):
            shutil.copy(tmp_save_path, save_path)



def synthesis_sound_async(mode, save_path, context, role_id, sample_sound_path, sample_text):
    threading.Thread(target=synthesis_sound, daemon=True,
                     args=(mode, save_path, context, role_id, sample_sound_path, sample_text)).start()

if __name__ == "__main__":
    synthesis_sound(0, 'Hello, word!',
              "c578d8d6f60f4471aec26ee233d2a7ad",
              "brian.mp3",
              """So, what was Brittany Babbitt like? Oh, you know, at Applebee's she's all like, "Hi, may I take your order? " And at her bedroom window she's all like, "Ah, get out of here". how'd you find my apartment? Tale of two Brittanys, huh? Yeah, I mean, if you don't want me showing up at your house, don't put a smiley face on my receipt. Uh, your honor, the defense rests. See, you get it.
                                    Have you read my book yet? I'm downloading it right now. It's beautiful. Yeah, this is, this is fine.
                                    This isn't, this isn't weird. I'm a robot you.""",
              )