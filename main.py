import os
import getopt
import traceback
import cfscrape
import datetime
import pyperclip
import sys
from bs4 import BeautifulSoup
from time import sleep
from itertools import islice
from shutil import copyfile


def get_steam_id(string, string_num, file_path):
    id_line = 'LogOnline: Verbose: Mirrors: [FOnlineSessionMirrors::AddSessionPlayer] Session:GameSession' in string
    if not id_line:
        return None
    id_number = string[len(string)::-1].split('|')[0]
    id_number = int(id_number[len(id_number)::-1])

    # All killer outfits tags
    killer_tags = ["CA", "GK", "QK", "DO", "BE", "SD", "FK", "OK", "UK", "WI", "HK", "TC", "KK", "MK", "MM", "TN",
                   "SwedenKiller", "TR", "UkraineKiller", "TW", "Bear", "Bob", "Chuckles", "Clown", "HA", "HB",
                   "HillBilly", "Killer07", "Legion", "Nurse", "Plague", "S01", "Spirit", "WI", "Witch", "WR", "Wraith"]

    # Wait for logs
    while get_file_length(path) < string_num + 10:
        pass

    killer_tag_line = [str(s_line) for s_line in islice(open(file_path, encoding='utf-8'), string_num, string_num + 10)]

    for kt_line in killer_tag_line:

        if 'LogCustomization: -->' in kt_line:
            debug_log(f'Line: {lines_counter}, kt_line: {kt_line}')
            for tag in killer_tags:
                if tag in kt_line:
                    return id_number
            else:
                return None
    else:
        return None


def get_host_info(host_id):
    scraper = cfscrape.create_scraper()
    request = None
    try:
        request = scraper.get(f'https://steamid.io/lookup/{str(host_id)}').text

    except Exception as e:
        with open('./error.log', 'a') as error_log:
            exc_type, exc_value, exc_traceback = sys.exc_info()

            error_log.write(f'[{datetime.datetime.now()}] Ignoring exception: ')
            for line in traceback.format_exception(exc_type, exc_value, exc_traceback):
                error_log.write(line)
        return ['No info', 'No info']
    soup = BeautifulSoup(request, features="html.parser")
    data = soup.find('section', {'id': 'content'})
    soup = BeautifulSoup(str(data), features="html.parser")
    error = soup.find('p', {'class': 'notice alert-danger'})
    soup = BeautifulSoup(request, features="html.parser")
    if error:
        return ['No info', 'No info']
    data = soup.find_all('dd', {'class': 'value'})
    soup = BeautifulSoup(str(data[len(data) - 1]), features="html.parser")
    link = str(soup.find('a').contents)[2:-2]
    name = str(data[len(data) - 4].contents)[2:-2]
    return [link, name]


def get_killer(string):
    killer_line = 'Spawn new pawn characterId 2684354' in string
    if not killer_line:
        return None
    killer_id = string[len(string)::-1].split(' ')[0]
    killer_id = killer_id[len(killer_id)::-1][7:-2]

    killers_dict = {'56': 'Trapper',
                    '57': 'Wraith',
                    '58': 'Hillbilly',
                    '59': 'Nurse',
                    '60': 'Hag',
                    '61': 'Michael Myers',
                    '62': 'Doctor',
                    '63': 'Huntress',
                    '64': 'Cannibal',
                    '65': 'Freddy',
                    '66': 'Pig',
                    '67': 'Clown',
                    '68': 'Spirit',
                    '69': 'Legion',
                    '70': 'Plague',
                    '71': 'GhostFace',
                    '72': 'Demogorgon',
                    '73': 'Oni',
                    '74': 'Deathslinger'}

    if killer_id in killers_dict.keys():
        return killers_dict[killer_id]
    else:
        return f'Unknown killer (id {killer_id})'


def get_in_menu_state(string):
    state = '[PartyContextComponent::UpdateReadyButtonStateInfo] Ready button updated : 0.' in string
    if state:
        return True
    else:
        return False


def get_file_length(filename):
    lines = 0
    for l_line in open(filename, encoding='utf-8'):
        lines += 1
    return lines


def debug_log(msg):
    if not debug:
        return
    with open(f'./debug-{start_time}/scanner.log', 'a') as log_file:
        log_file.write(msg + '\n')


def update_output(text):
    if os.name == 'nt' and not debug:
        os.system('cls')
    elif os.name != 'posix' and not debug:
        os.system('clear')
    print(text)


# Debug mode flag
debug = False
start_time = datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
try:
    opts, args = getopt.getopt(sys.argv[1:], 'd')
    for opt in opts:
        if opt[0] == '-d':
            debug = True
            os.mkdir(f'debug-{start_time}')
            log_file = open(f'./debug-{start_time}/scanner.log', 'w')
            log_file.close()

except getopt.GetoptError:
    pass

pre_read = False

if os.path.exists('./error.log'):
    os.remove('./error.log')

path = os.path.expandvars(r'%LOCALAPPDATA%') + '\DeadByDaylight\Saved\Logs\DeadByDaylight.log'
if not os.path.exists(path):
    print('Log file not found!')
    input()
    sys.exit()
else:
    # Clear old log if game not started yet
    try:
        log = open(path, 'w', encoding='utf-8')
        log.close()
    # If game already started, read previous log
    except PermissionError:
        pre_read = True

lines_counter = get_file_length(path)

# If game already started, read previous log
if pre_read:
    lines_counter = 0

info_displayed = False
id_num = None
killer_name = 'Unknown killer'
steam_data = ['No info', 'No info']

if debug:
    update_output('Running in debug mode! Waiting for game session... Press Ctrl+C to exit.')
else:
    update_output('Waiting for game session... Press Ctrl+C to exit.')

try:
    while True:
        if lines_counter != get_file_length(path):
            line_num = lines_counter

            for line in islice(open(path, encoding='utf-8'), line_num, None):

                if get_in_menu_state(line) and info_displayed:
                    debug_log(f'Line: {lines_counter}, in_menu_state call')
                    update_output('Waiting for game session... Press Ctrl+C to exit.')
                    id_num = None
                    killer_name = 'Unknown killer'
                    steam_data = ['No info', 'No info']
                    info_displayed = False
                    lines_counter += 1
                    continue

                parsed_id = get_steam_id(line, int(lines_counter), path)
                if id_num != parsed_id and parsed_id is not None:
                    debug_log(f'Line: {lines_counter}, get_steam_id call')
                    id_num = parsed_id
                    steam_data = get_host_info(id_num)
                    debug_log(f'Line: {lines_counter}, steam_id {id_num}')
                    debug_log(f'Line: {lines_counter}, team_id_info {steam_data}')
                    if steam_data[0] != 'No info':
                        pyperclip.copy(steam_data[0])
                    update_output(
                        f"In lobby.\nHost id: {id_num}\nProfile name: {steam_data[1]}\nKiller name: {killer_name}")
                    info_displayed = True

                parsed_killer_name = get_killer(line)
                if killer_name != parsed_killer_name and parsed_killer_name is not None:
                    debug_log(f'Line: {lines_counter}, get_killer_name call')
                    killer_name = parsed_killer_name
                    debug_log(f'Line: {lines_counter}, get_killer_name name = {killer_name}')
                    update_output(
                        f"In lobby.\nHost id: {id_num}\nProfile name: {steam_data[1]}\nKiller name: {killer_name}")
                    info_displayed = True

                lines_counter += 1
        sleep(3)

except KeyboardInterrupt:
    if debug:
        debug_log('Interrupted by user.')
        copyfile(path, f'./debug-{start_time}/game_log.log')

except Exception as e:
    print('Error has occurred see error.log for details!')
    with open('./error.log', 'a') as error_log:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error_log.write(f'[{datetime.datetime.now()}] Error: ')
        for line in traceback.format_exception(exc_type, exc_value, exc_traceback):
            error_log.write(line)
        error_log.write('Process terminated.')
    input()
