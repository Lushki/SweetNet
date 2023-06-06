import sys
import os
import subprocess


class EnvironmentConfigurator:
    def __init__(self, sys, os, subprocess):
        self.sys = sys
        self.os = os
        self.subprocess = subprocess

    def get_api_key(self, key_name):
        with open('ApiKeys.txt', 'r') as file:
            for line in file:
                if line.startswith(key_name):
                    return line.split('=')[1].strip()

    def get_google_maps_api_key(self):
        return self.get_api_key('GOOGLE_MAPS_API_KEY')

    def get_openai_api_key(self):
        return self.get_api_key('OPENAI_API_KEY')

    def get_settings(self, file_name):
        settings = {}
        with open(file_name, 'r') as file:
            for line in file:
                key, value = line.strip().split('=', 1)
                settings[key.strip()] = int(value.split('=')[1].split('weeks')[0].strip())
        return settings

    def config(self):
        if getattr(self.sys, 'real_prefix', self.sys.prefix) != self.sys.prefix:
            pass
        else:
            venv_path = self.os.path.join(self.os.getcwd(), 'venv')
            activate_script = self.os.path.join(venv_path, 'Scripts' if self.os.name == 'nt' else 'bin', 'activate')
            self.subprocess.call(activate_script, shell=True)
            self.subprocess.check_call([self.sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
