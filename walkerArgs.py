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

    parser.add_argument('-sm', '--screen_method', required=False, default=1, type=int,
                        help='Screen method to be used. 0 = RGC only, 1 = VNC only')

    # VNC
    parser.add_argument('-vncip', '--vnc_ip', required=False,
                        help='IP Address of VNC Server on Device.')
    parser.add_argument('-vncscr', '--vncscreen', type=int, default=None, required=False,
                        help='Screen Number of VNC Server on Device.')
    parser.add_argument('-vncport', '--vnc_port', type=int, required=False,
                        help='Port of VNC Server on Device.')
    parser.add_argument('-vncpassword', '--vnc_password', required=False,
                        help='Password of VNC Server on Device.')

    # MySQL
    parser.add_argument('-dbm', '--db_method', required=False,
                        help='DB scheme to be used. Either "monocle" or "rm".')
    parser.add_argument('-dbip', '--dbip', required=False,
                        help='IP of MySql Server.')
    parser.add_argument('-dbuser', '--dbusername', required=False,
                        help='Username of MySql Server.')
    parser.add_argument('-dbpassw', '--dbpassword', required=False,
                        help='Password of MySql Server.')
    parser.add_argument('-dbname', '--dbname', required=False,
                        help='Name of MySql Database.')
    parser.add_argument('-dbport', '--dbport', type=int, default=3306,
                        help='Port of MySql Server.')

    # TELNET
    parser.add_argument('-telip', '--tel_ip', required=False,
                        help='IP of the telnet server. String!')
    parser.add_argument('-telport', '--tel_port', required=False, type=int,
                        help='Port of the telnet server. Integer!')
    parser.add_argument('-telpassword', '--tel_password', required=False,
                        help='Password of the telnet server. String!')
    parser.add_argument('-ts', '--tel_timeout_socket', required=False, type=int, default=30,
                        help='The telnet socket\'s timeout. Int seconds.')
    parser.add_argument('-tc', '--tel_timeout_command', required=False, type=int, default=15,
                        help='The max time to wait for a command to return. Int seconds.')

    # Device specifics
    parser.add_argument('-sw', '--screen_width', type=int, required=False,
                        help='The mobile\'s screen width')
    parser.add_argument('-sh', '--screen_height', type=int, required=False,
                        help='The mobile\'s screen height')

    # CSV for Coords
    parser.add_argument('-file', '--file', required=False,
                        help='Full path to the .csv containing the gym coordinates.')

    # Walk Settings
    parser.add_argument('-s', '--speed', required=False, type=int, default=50,
                        help='The speed to walk from gym to gym in kmph. speed=0 means teleportation. Default: 50')
    parser.add_argument('-m', '--max_distance', required=False, type=int,
                        help=(
                            'The maximum distance [meters] to be walked. Anything with a longer distance to will be '
                            'teleported to. 0 or commented -> never teleport'))
    parser.add_argument('-gd', '--gym_distance', required=False, type=float, default=490.0,
                        help='The maximum distance [meters] to sum up gyms around a given gym. Default: 490.0')
    parser.add_argument('-mcg', '--max_count_gym_sum_up_around_gym', required=False, type=int, default=5,
                        help='The maximum distance [meters] to sum up gyms around a given gym. Default: 5')
    parser.add_argument('-ptd', '--post_teleport_delay', required=False, type=float, default=4.0,
                        help='The delay in seconds to wait after a teleport. Default: 4.0')
    parser.add_argument('-pwd', '--post_walk_delay', required=False, type=float, default=2.0,
                        help='The delay in seconds to wait after reaching a destination when walking. Default: 2.0')
    parser.add_argument('-psd', '--post_screenshot_delay', required=False, type=float, default=0.2,
                        help=(
                            'The delay in seconds to wait after taking a screenshot to copy it and start the next '
                            'round. Default: 0.2'))
    parser.add_argument('-rp', '--restart_pogo', required=False, type=int, default=80,
                        help='The amount of location-changes/scan-locations inbetween pogo restarts. Default: 80')
    parser.add_argument('-ptsod', '--post_turn_screen_on_delay', required=False, type=float, default=7.0,
                        help='The delay in seconds to wait after sending the turn screen on command. Default: 7.0')
    parser.add_argument('-ppsd', '--post_pogo_start_delay', required=False, type=float, default=60.0,
                        help='The delay in seconds to wait after starting pogo. Default: 60.0')
    parser.add_argument('-dah', '--delay_after_hatch', required=False, type=float, default=3.5,
                        help=(
                            'The delay in minutes to wait after an egg has hatched to move to the location of the '
                            'gym. Default: 3.5'))
    parser.add_argument('-watd', '--walk_after_teleport_distance', required=False, type=int, default=0,
                        help=(
                            'The walk a couple meters after a teleport covering a greater distance than this value. '
                            'Supposedly helps with loading'))
    parser.add_argument('-cds', '--cool_down_sleep', action='store_true', default=False,
                        help='Sleep for cooldown after teleport.')

    # Runtypes
    parser.add_argument('-os', '--only_scan', action='store_true', default=False,
                        help='Use this instance only for scanning.')
    parser.add_argument('-oo', '--only_ocr', action='store_true', default=False,
                        help='Use this instance only for OCR.')
    parser.add_argument('-om', '--ocr_multitask', action='store_true', default=False,
                        help='Running OCR in sub-processes (module multiprocessing) to speed up analysis of raids.')
    parser.add_argument('-wm', '--with_madmin', action='store_true', default=False,
                        help='Start madmin as instance.')

    # folder
    parser.add_argument('-tmp', '--temp_path', default='temp',
                        help='Temp Folder for OCR Scanning. Default: temp')

    parser.add_argument('-pgasset', '--pogoasset', required=True,
                        help=('Path to Pogo Asset.'
                              'See https://github.com/ZeChrales/PogoAssets/'))

    parser.add_argument('-rscrpath', '--raidscreen_path', default='screenshots',
                        help='Folder for processed Raidscreens. Default: screenshots')

    parser.add_argument('-ssvpath', '--successsave_path', default='success',
                        help='Folder for saved Raidcrops. Default: success')

    parser.add_argument('-unkpath', '--unknown_path', default='unknown',
                        help='Folder for unknows Gyms or Mons. Default: unknown')

    # div. settings

    parser.add_argument('-clnupa', '--cleanup_age', default='1440',
                        help='Delete Screenshots older than X minutes. Default: 1440')

    parser.add_argument('-gdv', '--gym_detection_value', default='0.75', type=float,
                        help=(
                            'Value of gym detection. The higher the more accurate is checked. 0.65 maybe generate '
                            'more false positive. Default: 0.75'))

    parser.add_argument('-ssv', '--save_success', action='store_true', default=False,
                        help='Save success submitted raidcrops.')

    parser.add_argument('-lc', '--last_scanned', action='store_true', default=False,
                        help='Submit last scanned location to RM DB (if supported). Default: False')

    parser.add_argument('-gsd', '--gym_scan_distance', type=float, default=6.0,
                        help='Search for nearby Gmy within this radius (in KM!!). '
                        'In areas with many Gyms reduce this argument to 1-2 Default: 6')
                        
    parser.add_argument('-npmf', '--npmFrom', type=float, default=0.8,
                        help='Matching zoom start value for mon! (Based on resolution)')
    parser.add_argument('-npmv', '--npmValue', type=float, default=2.0,
                        help='Matching zoom max value for mon! (Based on resolution)')

    parser.add_argument('-npv', '--npValue', type=float, default=0.5,
                        help='Matching zoom max value. (Based on resolution)')

    parser.add_argument('-npf', '--npFrom', type=float, default=0.2,
                        help='Matching zoom start value. (Based on resolution)')

    # Cleanup Hash Database
    parser.add_argument('-chd', '--clean_hash_database', action='store_true', default=False,
                        help='Cleanup the hashing database.')

    # timezone
    parser.add_argument('-tz', '--timezone', type=int, required=True,
                        help='Hours Difference to GMT0. f.e.: +2 for Berlin/Germany')

    # sleeptimer
    parser.add_argument('-st', '--sleeptimer', action='store_true', default=False,
                        help='Active the Sleeptimer.')
    parser.add_argument('-si', '--sleepinterval', default=[], action='append',
                        help='Intervals for the sleeptimer. f.e. [[22:00, 5:00]]')

    # download coords
    parser.add_argument('-latlngleft', '--latlngleft', default=[], action='append',
                        help='download gym coords from this param f.e. [47.1, 47.2]')
    parser.add_argument('-latlngright', '--latlngright', default=[], action='append',
                        help='download gym coords to this param  f.e. [9.1, 9.5]')
    parser.add_argument('-jj', '--justjson', action='store_true', default=False,
                        help='just generate the gym_info.json')

    # webhook
    parser.add_argument('-wh', '--webhook', action='store_true', default=False,
                        help='Active webhook support')
    parser.add_argument('-whurl', '--webhook_url', default='',
                        help='URL to receive webhooks')
    parser.add_argument('-wwh', '--weather_webhook', action='store_true', default=False,
                        help='Active weather webhook support')
    # weather
    parser.add_argument('-w', '--weather', action='store_true', default=False,
                        help='Read weather and post to db - if supported! (Default: False)')

    # MADmin
    parser.add_argument('-mmt', '--madmin_time', default='24',
                        help='MADmin clock format (12/24) (Default: 24)')

    parser.add_argument('-mmsc', '--madmin_sort', default='6',
                        help='MADmin sort column Raid/Gym (5= Modify / 6 = Create) (Default: 6)')

    parser.add_argument('-mmprt', '--madmin_port', default='5000',
                        help='MADmin web port (Default: 5000)')

    parser.add_argument('-mmnrsp', '--madmin_noresponsive', action='store_false', default=True,
                        help='MADmin deactivate responsive tables')

    parser.add_argument('-rfile', '--route_file', default='route',
                        help='Filename for Route Cache without extension (Default: route)')

    parser.add_argument('-pfile', '--position_file', default='current',
                        help='Filename for bot\'s current position (Default: current)')

    # Geofences
    parser.add_argument('-gf', '--geofence-file',
                        help=('Geofence file to define outer borders of the ' +
                              'scan area.'),
                        default='')
    parser.add_argument('-gef', '--geofence-excluded-file',
                        help=('File to define excluded areas inside scan ' +
                              'area. Regarded this as inverted geofence. ' +
                              'Can be combined with geofence-file.'),
                        default='')

    # etc

    parser.add_argument('-rdt', '--raid_time', default='45', type=int,
                        help='Raid Battle time in minutes. (Default: 45)')

    # log settings
    parser.add_argument('--no-file-logs',
                        help=('Disable logging to files. ' +
                              'Does not disable --access-logs.'),
                        action='store_true', default=False)
    parser.add_argument('--log-path',
                        help='Defines directory to save log files to.',
                        default='logs/')
    parser.add_argument('--log-filename',
                        help=('Defines the log filename to be saved.'
                              ' Allows date formatting, and replaces <SN>'
                              " with the instance's status name. Read the"
                              ' python time module docs for details.'
                              ' Default: %%Y%%m%%d_%%H%%M_<SN>.log.'),
                        default='%Y%m%d_%H%M_<SN>.log')
    parser.add_argument('-sn', '--status-name', default=str(os.getpid()),
                        help=('Enable status page database update using ' +
                              'STATUS_NAME as main worker name.'))

    parser.add_argument('-ah', '--auto_hatch', action='store_true', default=False,
                        help='Active auto hatch of level 5 eggs')

    parser.add_argument('-ahn', '--auto_hatch_number', type=int, default=0,
                        help='Auto hatch of level 5 Pokemon ID')

    parser.add_argument('--no_initial_restart', default=False,
                        help='Disable automatic PoGo restart when walker initially starts. NOT recommended.')

    verbose = parser.add_mutually_exclusive_group()
    verbose.add_argument('-v',
                         help='Show debug messages',
                         action='count', default=0, dest='verbose')
    verbose.add_argument('--verbosity',
                         help='Show debug messages',
                         type=int, dest='verbose')
    parser.set_defaults(DEBUG=False)

    args = parser.parse_args()
    # Allow status name and date formatting in log filename.
    args.log_filename = strftime(args.log_filename)
    args.log_filename = args.log_filename.replace('<sn>', '<SN>')
    args.log_filename = args.log_filename.replace('<SN>', args.status_name)

    return args
