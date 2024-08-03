import os
import threading
import time
import glob
import speech_recognition as sr
from kivy.app import App
from kivy.metrics import dp 
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
import spacy 
import shutil

nlp = spacy.load("en_core_web_sm")

middle_x, middle_y = Window.center

folder_name = time.strftime("diaryentry_%Y%m%d-%H%M%S")

class LoginScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.orientation = "vertical"

        # create widgets for the login screen
        self.password_label = Label(text="Enter Password:", font_name="Arial", font_size=40)
        self.password_input = TextInput(multiline=False, password=True)
        self.submit_button = Button(text="Submit", font_name="Arial", font_size=30, on_press=self.check_password)

        # add widgets to the layout
        self.add_widget(self.password_label)
        self.add_widget(self.password_input)
        self.add_widget(self.submit_button)

    def check_password(self, instance):
        password = self.password_input.text

        # read the stored password from the file
        stored_password = self.read_password_from_file()

        # check the password
        if password == stored_password:
            # if password is correct, remove login screen and go to main screen
            self.clear_widgets()
            self.add_widget(MainScreen())
        else:
            # if password is incorrect, clear the input field and display an error message
            self.password_input.text = ""
            self.password_label.text = "Incorrect Password, Try Again:"

    def read_password_from_file(self):
        password_file = "password.txt"

        try:
            with open(password_file, "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return ""

    def write_password_to_file(self, new_password):
        password_file = "password.txt"

        with open(password_file, "w") as f:
            f.write(new_password)


class ChangePasswordScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.orientation = "vertical"

        # create widgets for the change password screen
        self.old_password_label = Label(text="Enter Old Password:", font_name="Arial", font_size=40)
        self.old_password_input = TextInput(multiline=False, password=True)
        self.new_password_label = Label(text="Enter New Password:", font_name="Arial", font_size=40)
        self.new_password_input = TextInput(multiline=False, password=True)
        self.submit_button = Button(text="Submit", font_name="Arial", font_size=30, on_press=self.change_password)
        self.back_button = Button(text="Back", font_name="Arial", font_size=30, on_press=self.go_to_main_screen)

        # add widgets to the layout
        self.add_widget(self.old_password_label)
        self.add_widget(self.old_password_input)
        self.add_widget(self.new_password_label)
        self.add_widget(self.new_password_input)
        self.add_widget(self.submit_button)
        self.add_widget(self.back_button)

    def change_password(self, instance):
        old_password = self.old_password_input.text
        new_password = self.new_password_input.text

        # read the stored password from the file
        stored_password = LoginScreen().read_password_from_file()

        # check the old password
        if old_password == stored_password:
            # write the new password to the file
            LoginScreen().write_password_to_file(new_password)

            # clear input fields
            self.old_password_input.text = ""
            self.new_password_input.text = ""

            # display success message
            self.old_password_label.text = "Password changed successfully!"
        else:
            # clear input fields and display an error message
            self.old_password_input.text = ""
            self.new_password_input.text = ""
            self.old_password_label.text = "Incorrect password, Try Again:"

    def go_to_main_screen(self, instance):
        self.clear_widgets()
        self.add_widget(MainScreen())


class RecordScreen(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.listener = sr.Recognizer()
        self.recording = False
        self.filename = None
        self.recording_thread = None
        self.audio = None

        # UI elements
        self.label = Label(text="Press Record to start recording", pos=(500, 600), size=(400, 50),font_size=30)
        self.add_widget(self.label)

        self.record_button = Button(text="Record", pos=(400, 480), size=(200, 100))
        self.record_button.bind(on_press=self.start_recording)
        self.add_widget(self.record_button)

        self.stop_button = Button(text="Stop", pos=(800, 480), size=(200, 100))
        self.stop_button.bind(on_press=self.stop_recording)
        self.add_widget(self.stop_button)

        self.label = Label(text="Enter text entry", pos=(500, 400), size=(400, 50),font_size=30)
        self.add_widget(self.label)

        self.text_input = TextInput(pos=(100, 200), size=(1170, 170))
        self.add_widget(self.text_input)

        self.save_button = Button(text="Save", pos=(600, 80), size=(200, 100))
        self.save_button.bind(on_press=self.save_text_input)
        self.add_widget(self.save_button)

        self.back_button = Button(text="Back to Main Screen", pos=(200, 100), size=(200, 50))
        self.back_button.bind(on_press=self.go_to_main_screen)
        self.add_widget(self.back_button)

    def save_text_input(self, instance):
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)
        filename = os.path.join(folder_name, "text_input.txt")
        text = self.text_input.text
        with open(filename, "w") as f:
            f.write(text)
        self.text_input.text = ""

    def start_recording(self, instance):
        self.recording = True
        
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)
        self.filename = os.path.join(folder_name, f"recording-{time.strftime('%Y%m%d-%H%M%S')}.wav")
        self.recording_thread = threading.Thread(target=self.record_audio)
        self.recording_thread.start()

    def stop_recording(self, instance):
        self.recording = False

        if self.audio is not None:
            with open(self.filename, "wb") as f:
                f.write(self.audio.get_wav_data())

            self.label.text = f"Recorded to {self.filename}"

            try:
                self.label.text = "Converting audio to text..."
                text = self.listener.recognize_google(self.audio)
                text_filename = f"{os.path.splitext(self.filename)[0]}.txt"
                with open(text_filename, "w") as f:
                    f.write(text)
                    
                doc = nlp(text)
                entities = [(ent.text, ent.label_) for ent in doc.ents]
                entities_filename = f"{os.path.splitext(self.filename)[0]}_entities.txt"
                with open(entities_filename, "w") as f:
                    for entity in entities:
                        if entity[1] != "":
                            f.write(f"{entity[0]}: {entity[1]}\n")

                self.label.text = f"Recorded to {self.filename}, \n and saved as {text_filename} and {entities_filename}"
            except sr.UnknownValueError:
                self.label.text = "Google Speech Recognition could not understand audio"
            except sr.RequestError as e:
                self.label.text = f"Could not request results from Google Speech Recognition service; {e}"
        else:
            self.label.text = "Error: Audio not recorded properly"



    def record_audio(self):
        with sr.Microphone() as source:
            self.listener.adjust_for_ambient_noise(source, duration=1)
            self.label.text = "Recording..."
            self.audio = self.listener.listen(source)


    def go_to_main_screen(self, instance):
        parent = self.parent
        if parent is not None:
            parent.clear_widgets()
            parent.add_widget(MainScreen())

class ViewRecordsScreen(BoxLayout):
    dir_path = "D:\\EDAI2"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # UI elements
        self.orientation = "vertical"

        self.label = Label(text="Records", font_size=30, size_hint=(1, 0.3),color=(0,0,0,1))

        self.add_widget(self.label)

        self.scroll_view = ScrollView()
        self.grid_layout = GridLayout(cols=3, spacing=10, size_hint_y=None)
        self.grid_layout.bind(minimum_height=self.grid_layout.setter('height'))
        self.scroll_view.add_widget(self.grid_layout)
        self.add_widget(self.scroll_view)

        self.back_button = Button(text="Back to Main Screen", font_size=30, size_hint=(1, 0.3), height=50)
        self.back_button.bind(on_press=self.go_to_main_screen)
        self.add_widget(self.back_button)

        # Load recorded folders
        self.folders = []
        for folder_name in os.listdir(self.dir_path):
            if folder_name.startswith("diary"):
                folder_path = os.path.join(self.dir_path, folder_name)
                if os.path.isdir(folder_path):
                    self.folders.append(folder_name)


        # Add each folder to the grid layout with delete button
        for folder_name in self.folders:
            folder_box = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=50)

            button = Button(text=f"{folder_name}", size_hint=(0.7, 1))
            button.folder_name = folder_name
            button.bind(on_press=self.open_folder)

            delete_button = Button(text="Delete", size_hint=(0.3, 1), background_color=(1, 0, 0, 1))
            delete_button.folder_name = folder_name
            delete_button.bind(on_press=self.delete_folder)

            folder_box.add_widget(button)
            folder_box.add_widget(delete_button)
            self.grid_layout.add_widget(folder_box)

    def open_folder(self, instance):
        folder_name = instance.folder_name
        folder_path = os.path.join(self.dir_path, folder_name)

        # Create a new instance of ViewFolderScreen and add it as a child to the parent
        parent = self.parent
        parent.remove_widget(self)
        parent.add_widget(ViewFolderScreen(folder_path, folder_name))

    def delete_folder(self, instance):
        folder_name = instance.folder_name
        folder_path = os.path.join(self.dir_path, folder_name)

        # Remove the folder and its contents
        shutil.rmtree(folder_path)

        # Remove the folder from the list and update the grid layout
        self.folders.remove(folder_name)
        self.grid_layout.clear_widgets()

        for folder_name in self.folders:
            folder_box = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=50)

            button = Button(text=f"{folder_name}", size_hint=(0.7, 1))
            button.folder_name = folder_name
            button.bind(on_press=self.open_folder)

            delete_button = Button(text="Delete", size_hint=(0.3, 1), background_color=(1, 0, 0, 1))
            delete_button.folder_name = folder_name
            delete_button.bind(on_press=self.delete_folder)

            folder_box.add_widget(button)
            folder_box.add_widget(delete_button)
            self.grid_layout.add_widget(folder_box)

    def go_to_main_screen(self, instance):
        parent = self.parent
        if parent is not None:
            parent.clear_widgets()
            parent.add_widget(MainScreen())


class ViewFolderScreen(BoxLayout):
    def __init__(self, folder_path, folder_name, **kwargs):
        super().__init__(**kwargs)

        self.orientation = "vertical"

        self.label = Label(text=folder_name,font_size=30, size_hint_y=0.5, height=20, color=(0,0,0,1))
        self.add_widget(self.label)

        self.grid_layout = GridLayout(cols=2, spacing=50, size_hint_y=None)
        self.grid_layout.bind(minimum_height=self.grid_layout.setter('height'))

        self.recordings = []
        for filename in glob.glob(os.path.join(folder_path, "*.wav")):
            transcript_filename = f"{os.path.splitext(filename)[0]}_entities.txt"
            if os.path.isfile(transcript_filename):
                with open(transcript_filename, "r") as f:
                    entities = f.read().strip()
            else:
                entities = "<No entities available>"

            text_filename = f"{os.path.splitext(filename)[0]}.txt"
            if os.path.isfile(text_filename):
                with open(text_filename, "r") as f:
                    transcript = f.read()
            else:
                transcript = "<No transcript available>"
            self.recordings.append((filename, transcript, entities))

        for i, (filename, transcript, entities) in enumerate(self.recordings):
            filename_label = Label(text=os.path.basename(filename), size_hint_y=None, height=dp(50), color=(0,0,0,1))
            play_button = Button(text="Play", size_hint_y=None, height=dp(50), font_size=20)
            play_button.filename = filename
            play_button.bind(on_press=self.play_audio)
            transcript_label = Label(text=transcript, size_hint_y=None, height=dp(50), halign="center", valign="bottom", font_size=20, color=(0,0,0,1))
            transcript_label.text_size = (self.width+dp(500), None) # adjust width based on available space
            self.grid_layout.add_widget(filename_label)
            self.grid_layout.add_widget(play_button)
            self.grid_layout.add_widget(transcript_label)
            if entities != "<No entities available>":
                entities_label = Label(text=f"Entities: {entities}", size_hint_y=None, height=dp(50), halign="center", valign="bottom", font_size=20, color=(0,0,0,1))
                entities_label.text_size = (self.width+dp(500), None) # adjust width based on available space
                self.grid_layout.add_widget(entities_label)



        self.scroll_view = ScrollView(size_hint=(1, None), size=(Window.width, Window.height - 200))
        self.scroll_view.add_widget(self.grid_layout)
        self.add_widget(self.scroll_view)

        text_input_filename = os.path.join(folder_path, "text_input.txt")

        text_input_contents = "<No text entry available>"

        for filename in glob.glob(os.path.join(folder_path, "*.txt")):
            if filename == text_input_filename:
                with open(filename, "r") as f:
                    text_input_contents = f.read().strip()
                break

        self.text_input_label = Label(text=text_input_contents, font_size=20, size_hint_y=1, height=50, halign="left", valign="bottom",color=(0,0,0,1))
        self.add_widget(self.text_input_label)

        self.back_button = Button(text="Back to Records", size_hint_y=None, height=50)
        self.back_button.bind(on_press=self.go_to_records_screen)
        self.add_widget(self.back_button)


    def go_to_records_screen(self, instance):
        parent = self.parent
        parent.remove_widget(self)
        parent.add_widget(ViewRecordsScreen())

    def play_audio(self, instance):
        sound = SoundLoader.load(instance.filename)
        if sound is not None:
            sound.play()


class change_color_screen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"

        self.label = Label(text="Change Color Theme", font_size=30)
        self.color_options = [
            (0.631, 0.745, 0.788, 1),  # Default color
            (0.373, 0.431, 0.553, 1),  # Red color
            (0.992, 0.863, 0.361, 1),  # Green color
            (1, 0.753, 0.796, 1)  # Blue color
        ]

        self.color_buttons = []
        for color in self.color_options:
            color_button = Button(text="Color Option", background_color=color)
            color_button.bind(on_press=self.change_background_color)
            self.color_buttons.append(color_button)
            self.add_widget(color_button)

        self.back_button = Button(text="Back to Main Screen", font_size=20)
        self.back_button.bind(on_press=self.go_to_main_screen)
        self.add_widget(self.back_button)

    def change_background_color(self, instance):
        selected_color = instance.background_color
        Window.clearcolor = selected_color

        # Save the selected color to a file
        with open("color_choice.txt", "w") as f:
            f.truncate(0)
            f.write(', '.join(str(c) for c in selected_color))


    def go_to_main_screen(self, instance):
        self.clear_widgets()
        self.add_widget(MainScreen())  # Assuming you have a MainScreen class defined


class MainScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.orientation = "vertical"

        # create widgets for the main screen
        self.label = Label(text="Hello! Select an option:", font_name='Georgia', font_size=40, color=(0,0,0,1))
        self.add_record_button = Button(text="Add Record", font_size=30)
        self.view_records_button = Button(text="View Records", font_size=30)
        self.change_password_button = Button(text="Change Password", font_size=30, size_hint_y=0.5)
        self.changecolor_button= Button(text="Change Theme", font_size=30, size_hint_y=0.5)
        self.change_password_button.background_color = (1, 0, 0, 1)
        self.changecolor_button.background_color=  (0.690, 1, 0.678, 1)  # Set background color to red (RGBA values: 1, 0, 0, 1)

        # bind button actions
        self.add_record_button.bind(on_press=self.go_to_record_screen)
        self.view_records_button.bind(on_press=self.go_to_view_records_screen)
        self.change_password_button.bind(on_press=self.go_to_change_password_screen)
        self.changecolor_button.bind(on_press=self.go_to_color)

        # add widgets to the layout
        self.add_widget(self.label)
        self.add_widget(self.add_record_button)
        self.add_widget(self.view_records_button)
        self.add_widget(self.change_password_button)
        self.add_widget(self.changecolor_button)

    def go_to_record_screen(self, instance):
        self.clear_widgets()
        self.add_widget(RecordScreen())

    def go_to_view_records_screen(self, instance):
        self.clear_widgets()
        self.add_widget(ViewRecordsScreen())

    def go_to_change_password_screen(self, instance):
        self.clear_widgets()
        self.add_widget(ChangePasswordScreen())
    
    def go_to_color(self, instance):
        self.clear_widgets()
        self.add_widget(change_color_screen())

    def on_size(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            color = self.load_color_choice()
            Color(*color)
            Rectangle(pos=self.pos, size=self.size)

    def load_color_choice(self):
        default_color = (0.631, 0.745, 0.788, 1)  # Default color if file is not found or invalid
        try:
            with open("color_choice.txt", "r") as f:
                color_str = f.read().strip()
                color_values = color_str.split(',')
                if len(color_values) == 4:
                    color = tuple(float(value) for value in color_values)
                    return color
        except FileNotFoundError:
            pass
        return default_color




class RecorderApp(App):
    def build(self):
        return LoginScreen()

if __name__ == "__main__":
    RecorderApp().run()
