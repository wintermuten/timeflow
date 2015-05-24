from datetime import datetime as dt
import os
import subprocess


LOG_FILE = os.path.expanduser('~') + '/.timelog/timeflow'
DATETIME_FORMAT = "%Y-%m-%d %H:%M"
DATE_FORMAT = "%Y-%m-%d"
# length of date string
DATE_LEN = 10
# length of datetime string
DATETIME_LEN = 16


def write_to_log_file(message):
    log_message = form_log_message(message)
    if not os.path.exists(os.path.dirname(LOG_FILE)):
        os.makedirs(os.path.dirname(LOG_FILE))
    with open(LOG_FILE, 'a') as fp:
        fp.write(log_message)


def read_log_file_lines():
    with open(LOG_FILE, 'r') as fp:
        return [line for line in fp.readlines() if line != '\n']


def form_log_message(message):
    time_str = dt.now().strftime(DATETIME_FORMAT)
    log_message = ': '.join((time_str, message))
    if is_another_day():
        return '\n' + log_message + '\n'
    else:
        return log_message + '\n'


def is_another_day():
    """
    Checks if new message is written in the next day,
    than the last log entry.

    date - message date
    """
    try:
        f = open(LOG_FILE, 'r')
        last_line = f.readlines()[-1]
    except (IOError, IndexError):
        return False

    last_log_date = last_line[:DATE_LEN]

    # if message date is other day than last log entry return True, else False
    if dt.now().strftime(DATE_FORMAT) != last_log_date:
        return True
    else:
        return False


def find_date_line(lines, date_to_find, reverse=False):
    "Returns line index of lines, with date_to_find"
    len_lines = len(lines) - 1
    if reverse:
        lines = reversed(lines)
    for i, line in enumerate(lines):
        date_obj = dt.strptime(line[:DATE_LEN], DATE_FORMAT)
        date_to_find_obj = dt.strptime(date_to_find, DATE_FORMAT)

        if reverse and date_obj <= date_to_find_obj:
            return len_lines - i
        elif not reverse and date_obj >= date_to_find_obj:
            return i


def date_begins(lines, date_to_find):
    "Returns first line out of lines, with date_to_find"
    return find_date_line(lines, date_to_find)


def date_ends(lines, date_to_find):
    "Returns last line out of lines, with date_to_find"
    return find_date_line(lines, date_to_find, reverse=True)


def is_arrived(line):
    "Returns True if log line marks beggining of the day"
    line = line.replace(' ', '').replace('\n', '').replace('.', '')
    if line[DATETIME_LEN:].lower() == 'arrived':
        return True
    return False


def is_slack(line):
    "Returns True if current log line is slack"
    # slack entries end with '**' and can also have linefeed char
    line = line.replace(' ', '').replace('\n', '')
    if line[-2:] == "**":
        return True
    return False


def get_time(seconds):
    hours = seconds // 3600
    minutes = seconds % 3600 // 60
    return hours, minutes


def print_stats(work_time, slack_time):
    work_hours, work_minutes = get_time(sum(work_time))
    slack_hours, slack_minutes = get_time(sum(slack_time))

    work_string = 'Work: {:02}h {:02}min'.format(work_hours, work_minutes)
    slack_string = 'Slack: {:02}h {:02}min'.format(slack_hours, slack_minutes)

    subprocess.call(['echo', work_string])
    subprocess.call(['echo', slack_string])


def calculate_stats(lines, date_from, date_to):
    work_time = []
    slack_time = []

    line_begins = date_begins(lines, date_from)
    line_ends = date_ends(lines, date_to)

    date_not_found = (line_begins is None or line_ends < line_begins)
    if date_not_found:
        return work_time, slack_time

    for i, line in enumerate(lines[line_begins:line_ends+1]):
        # if we got to the last line - stop
        if line_begins+i+1 > line_ends:
            break

        next_line = lines[line_begins+i+1]

        line_time = dt.strptime(line[:DATETIME_LEN], DATETIME_FORMAT)
        if is_arrived(next_line):
            continue

        else:
            next_line_time = dt.strptime(next_line[:DATETIME_LEN],
                                         DATETIME_FORMAT)
            timedelta = (next_line_time - line_time).seconds

        if is_slack(next_line):
            slack_time.append(timedelta)
        else:
            work_time.append(timedelta)

    return work_time, slack_time