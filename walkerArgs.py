import sys
import os
import configargparse
import logging
from time import strftime

log = logging.getLogger(__name__)

def memoize(function):
    memo = {}

    def wrapper(*args):
        if args in memo:
            return memo[args]
        else:
            rv = function(*args)
            memo[args] = rv
            return rv
    return wrapper

@memoize
def parseArgs():
    defaultconfigfiles = []
    if '-cf' not in sys.argv and '--config' not in sys.argv:
        defaultconfigfiles = [os.getenv('THERAIDMAPPER_CONFIG', os.path.join(
            os.path.dirname(__file__), 'config.ini'))]
    parser = configargparse.ArgParser(
        default_config_files=defaultconfigfiles,
        auto_env_var_prefix='THERAIDMAPPER_')
    parser.add_argument('-cf', '--config',
            is_config_file=True, help='Set configuration file')

    #VNC
    parser.add_argument('-vncip', '--vnc_ip', required=False,
            help=('IP Address of VNC Server on Device.'))
    parser.add_argument('-vncscr', '--vncscreen', type=int, default=None, required=False,
            help=('Screen Number of VNC Server on Device.'))
    parser.add_argument('-vncport', '--vnc_port', type=int, required=False,
            help=('Port of VNC Server on Device.'))
    parser.add_argument('-vncpassword', '--vnc_password', required=False,
            help=('Password of VNC Server on Device.'))

    #MySQL
    parser.add_argument('-dbip', '--dbip', required=False,
            help=('IP of MySql Server.'))
    parser.add_argument('-dbuser', '--dbusername', required=False,
            help=('Username of MySql Server.'))
    parser.add_argument('-dbpassw', '--dbpassword', required=False,
            help=('Password of MySql Server.'))
    parser.add_argument('-dbname', '--dbname', required=False,
            help=('Name of MySql Database.'))
    parser.add_argument('-dbport', '--dbport', type=int, default=3306,
            help=('Port of MySql Server.'))

    #TELNET
    parser.add_argument('-telip', '--tel_ip', required=False,
            help=('IP of the telnet server. String!'))
    parser.add_argument('-telport', '--tel_port', required=False, type=int,
            help=('Port of the telnet server. Integer!'))
    parser.add_argument('-telpassword', '--tel_password', required=False,
            help=('Password of the telnet server. String!'))

    #Device specifics
    parser.add_argument('-sw', '--screen_width', type=int, required=True,
            help=('The mobile\'s screen width'))
    parser.add_argument('-sh', '--screen_height', type=int, required=True,
            help=('The mobile\'s screen height'))

    #CSV for Coords
    parser.add_argument('-file', '--file', required=False,
            help=('Full path to the .csv containing the gym coordinates.'))

    #Walk Settings
    parser.add_argument('-s', '--speed', required=False, type=int, default=50,
            help=('The speed to walk from gym to gym in kmph. speed=0 means teleportation. Default: 50'))
    parser.add_argument('-m', '--max_distance', required=False, type=int,
            help=('The maximum distance to be walked. Anything with a longer distance will be teleported to.'))


    #Runtypes
    parser.add_argument('-os', '--only_scan', action='store_true', default=False,
            help=('Use this instance only for scanning.'))
    parser.add_argument('-oo', '--only_ocr', action='store_true', default=False,
            help=('Use this instance only for OCR.'))
    parser.add_argument('-om', '--ocr_multitask', action='store_true', default=False,
            help=('Running OCR in sub-processes (module multiprocessing) to speed up analysis of raids.'))


    #folder
    parser.add_argument('-tmp', '--temp_path', default='temp',
            help=('Temp Folder for OCR Scanning. Defaul: temp'))

    parser.add_argument('-pgasset', '--pogoasset', required=True,
            help=('Path to Pogo Asset.'
                  'See https://github.com/ZeChrales/PogoAssets/'))

    parser.add_argument('-rscrpath', '--raidscreen_path', default='screenshots',
            help=('Folder for processed Raidscreens. Default: screenshots'))

    parser.add_argument('-unkpath', '--unknown_path', default='unknown',
            help=('Folder for unknows Gyms or Mons. Default: unknown'))


    # Egg - Mon placeholder
    parser.add_argument('-egg1mon', '--egg1_mon_id', default='15',
            help=('Mon Placeholder for Level 1. Default: 15'))
    parser.add_argument('-egg2mon', '--egg2_mon_id', default='20',
            help=('Mon Placeholder for Level 2. Default: 20'))
    parser.add_argument('-egg3mon', '--egg3_mon_id', default='55',
            help=('Mon Placeholder for Level 3. Default: 55'))
    parser.add_argument('-egg4mon', '--egg4_mon_id', default='164',
            help=('Mon Placeholder for Level 4. Default: 164'))
    parser.add_argument('-egg5mon', '--egg5_mon_id', default='198',
            help=('Mon Placeholder for Level 5. Default: 198'))

    # Cleanup Hash Database
    parser.add_argument('-chd', '--clean_hash_database', action='store_true', default=False,
            help=('Cleanup the hashing database.'))

    #timezone
    parser.add_argument('-tz', '--timezone', type=int, required=True,
            help=('Hours Difference to GMT0. f.e.: +2 for Berlin/Germany'))

    #sleeptimer
    parser.add_argument('-st', '--sleeptimer', action='store_true', default=False,
            help=('Active the Sleeptimer.'))
    parser.add_argument('-si', '--sleepinterval', default=[], action='append',
            help=('Intervalls for the sleeptimer. f.e. [[22:00, 5:00]]'))

    #download coords
    parser.add_argument('-latlngleft', '--latlngleft', default=[], action='append',
            help=('download gym cords from this param f.e. [47.1, 47.2]'))
    parser.add_argument('-latlngright', '--latlngright', default=[], action='append',
            help=('download gym cords to this param  f.e. [9.1, 9.5]'))

    #log settings
    parser.add_argument('--no-file-logs',
                        help=('Disable logging to files. ' +
                              'Does not disable --access-logs.'),
                        action='store_true', default=False)
    parser.add_argument('--log-path',
                        help=('Defines directory to save log files to.'),
                        default='logs/')
    parser.add_argument('--log-filename',
                        help=('Defines the log filename to be saved.'
                              ' Allows date formatting, and replaces <SN>'
                              " with the instance's status name. Read the"
                              ' python time module docs for details.'
                              ' Default: %%Y%%m%%d_%%H%%M_<SN>.log.'),
                        default='%Y%m%d_%H%M_<SN>.log'),
    parser.add_argument('-sn', '--status-name', default=str(os.getpid()),
                        help=('Enable status page database update using ' +
                              'STATUS_NAME as main worker name.'))
    verbose = parser.add_mutually_exclusive_group()
    verbose.add_argument('-v',
                         help=('Show debug messages'),
                         action='count', default=0, dest='verbose')
    verbose.add_argument('--verbosity',
                          help=('Show debug messages'),
                          type=int, dest='verbose')
    parser.set_defaults(DEBUG=False)

    args = parser.parse_args()
    # Allow status name and date formatting in log filename.
    args.log_filename = strftime(args.log_filename)
    args.log_filename = args.log_filename.replace('<sn>', '<SN>')
    args.log_filename = args.log_filename.replace('<SN>', args.status_name)


    return args
