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
def get_args():
    defaultconfig = []
    if '-cf' not in sys.argv and '--config' not in sys.argv:
        defaultconfigfiles = [os.getenv('THERAIDMAPPER_CONFIG', os.path.join(
        os.path.dirname(__file__), 'config.ini'))]   
    parser = configargparse.ArgParser(
        default_config_files=defaultconfigfiles,
        auto_env_var_prefix='THERAIDMAPPER_')
    parser.add_argument('-cf', '--config',
            is_config_file=True, help='Set configuration file')
    parser.add_argument('-vncip', '--vncip', required=True,
            help=('IP Address of VNC Server on Device.'))
    parser.add_argument('-vncscreen', '--vncscr', type=int, default=None, required=False,
            help=('Screen Number of VNC Server on Device.'))
    parser.add_argument('-vncport', '--vncprt', type=int, required=True,
            help=('Port of VNC Server on Device.'))
    parser.add_argument('-vncpassw', '--vncpwd', required=True,
            help=('Password of VNC Server on Device.'))
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
        
