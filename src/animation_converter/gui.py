import PySimpleGUI as sg
import subprocess
from pathlib import Path

def create_gui():
    # Define the layout
    layout = [
        [sg.Text('Input Files'), sg.Input(key='input_files'), sg.FilesBrowse()],
        [sg.Frame('Basic Options', [
            [sg.Text('Mode:'), sg.Combo(['petscii', 'animation'], key='mode', default_value='petscii')],
            [sg.Checkbox('Use Color', key='use_color')],
            [sg.Text('Border Color:'), sg.Input(key='border_color', size=(5,1))],
            [sg.Text('Background Color:'), sg.Input(key='background_color', size=(5,1))]
        ])],
        [sg.Frame('Advanced Options', [
            [sg.Text('Charset:'), sg.Input(key='charset'), sg.FileBrowse(file_types=(("Charset Files", "*.64c *.bin"),))],
            [sg.Text('Color Data:'), sg.Input(key='color_data'), sg.FileBrowse()],
            [sg.Text('Limit Charsets:'), sg.Input(key='limit_charsets', size=(5,1))],
            [sg.Text('Start Threshold:'), sg.Slider(range=(1,7), orientation='h', key='start_threshold')]
        ])],
        [sg.Frame('Animation Options', [
            [sg.Text('Animation Slowdown:'), sg.Input(key='anim_slowdown_frames', size=(5,1))],
            [sg.Text('Offset Color Frames:'), sg.Input(key='offset_color_frames', size=(5,1))],
            [sg.Text('Randomize Colors:'), sg.Input(key='randomize_color_frames', size=(5,1))]
        ])],
        [sg.Button('Convert'), sg.Button('Exit')]
    ]

    window = sg.Window('Animation Converter', layout)
    while True:
        event, values = window.read()
        
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
            
        #if event == 'Convert':
        #    if not values['input_files']:
        #        sg.popup_error('Please select input files')
        #        continue
        #        
        #    cmd = ['animation-tool']
        #    
        #    # Add all the options that have values
        #    if values['mode']: cmd.extend(['--mode', values['mode']])
        #    if values['use_color']: cmd.append('--use-color')
        #    if values['border_color']: cmd.extend(['--border-color', values['border_color']])
        #    if values['background_color']: cmd.extend(['--background-color', values['background_color']])
        #    if values['charset']: cmd.extend(['--charset', values['charset']])
        #    if values['color_data']: cmd.extend(['--color-data', values['color_data']])
        #    if values['limit_charsets']: cmd.extend(['--limit-charsets', values['limit_charsets']])
        #    if values['start_threshold']: cmd.extend(['--start-threshold', str(int(values['start_threshold']))])
        #    if values['anim_slowdown_frames']: cmd.extend(['--anim-slowdown-frames', values['anim_slowdown_frames']])
        #    if values['offset_color_frames']: cmd.extend(['--offset-color-frames', values['offset_color_frames']])
        #    if values['randomize_color_frames']: cmd.extend(['--randomize-color-frames', values['randomize_color_frames']])
        #    
        #    # Add input files at the end
        #    cmd.extend(values['input_files'].split(';'))
        #    
        #    try:
        #        result = subprocess.run(cmd, capture_output=True, text=True)
        #        if result.returncode == 0:
        #            sg.popup('Conversion Complete', result.stdout)
        #        else:
        #            sg.popup_error('Error during conversion', result.stderr)
        #    except Exception as e:
        #        sg.popup_error('Error running converter', str(e))

    window.close()