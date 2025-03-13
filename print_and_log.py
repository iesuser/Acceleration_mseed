import os, datetime

log_filename = "ies_acc_log"
script_path = os.path.dirname(os.path.realpath(__file__))

printing = True
write_in_log = True

def print_and_log(message, empty_line=False):
    log_file_path = script_path + "/" + log_filename
    pid  = os.getpid()
    if printing is True:
        print("[" + datetime.datetime.now().strftime('%Y-%m-%d %T') + "] [" + str(pid) + "] " + message)
    if write_in_log is True:
        with open(log_file_path, "a") as log_file:
            if not empty_line:
                log_file.write("[" + datetime.datetime.now().strftime('%Y-%m-%d %T') + "] [" + str(pid) + "] " + message + "\n")
            else:
                log_file.write("\n")