import argparse

def parseArgs():
    argParser = argparse.ArgumentParser()

    #help for each option
    helps = {}
    helps['file'] = 'Full path to the .csv containing the gym coordinates'
    helps['tel_ip'] = 'IP of the telnet server. String!'
    helps['tel_port'] = 'Port of the telnet server. Integer!'
    helps['tel_password'] = 'Password of the telnet server. String!'
    helps['vnc_ip'] = 'IP of the VNC server. String!'
    helps['vnc_port'] = 'Port of the VNC server. Integer!'
    helps['vnc_password'] = 'Password of the VNC server. String!'
    helps['speed'] = 'The speed to walk from gym to gym in kmph. speed=0 means teleportation. Default: 50'
    helps['max_distance'] = 'The maximum distance to be walked. Anything with a longer distance will be teleported to.'

    argParser.add_argument(
        '-f', '--file',
        help = helps['file'],
        required = True
    )

    argParser.add_argument(
        '--tel_ip',
        help = helps['tel_ip'],
        required = True
    )

    argParser.add_argument(
        '--tel_port',
        help = helps['tel_port'],
        required = True,
        type = int
    )

    argParser.add_argument(
        '--tel_password',
        help = helps['tel_password'],
        required = False
    )

    argParser.add_argument(
        '--vnc_ip',
        help = helps['vnc_ip'],
        required = True
    )

    argParser.add_argument(
        '--vnc_port',
        help = helps['vnc_port'],
        required = True,
        type = int
    )

    argParser.add_argument(
        '--vnc_password',
        help = helps['vnc_password'],
        required = False
    )

    argParser.add_argument(
        '-s', '--speed',
        help = helps['speed'],
        required = True,
        default = 50,
        type = int
    )

    argParser.add_argument(
        '-m', '--max_distance',
        help = helps['max_distance'],
        required = False,
        type = int
    )

    argParser.add_argument('-pgasset', '--pogoasset', required=True,
            help=('Path to Pogo Asset.'
                  'See https://github.com/ZeChrales/PogoAssets/'))

    argParser.add_argument('--no-file-logs',
                        help=('Disable logging to files. ' +
                              'Does not disable --access-logs.'),
                        action='store_true', default=False)
    argParser.add_argument('--log-path',
                        help=('Defines directory to save log files to.'),
                        default='logs/')
    argParser.add_argument('--log-filename',
                        help=('Defines the log filename to be saved.'
                              ' Allows date formatting, and replaces <SN>'
                              " with the instance's status name. Read the"
                              ' python time module docs for details.'
                              ' Default: %%Y%%m%%d_%%H%%M_<SN>.log.'),
                        default='%Y%m%d_%H%M_<SN>.log'),

    argParser.add_argument('-dbip', '--dbip', required=True,
            help=('IP of MySql Server.'))
    argParser.add_argument('-dbuser', '--dbusername', required=True,
            help=('Username of MySql Server.'))
    argParser.add_argument('-dbpassw', '--dbpassword', required=True,
            help=('Password of MySql Server.'))
    argParser.add_argument('-dbname', '--dbname', required=True,
            help=('Name of MySql Databsae.'))
    argParser.add_argument('-dbport', '--dbport', type=int, default=3306,
            help=('Port of MySql Server.'))

    verbose = argParser.add_mutually_exclusive_group()
    verbose.add_argument('-v',
                         help=('Show debug messages'),
                         action='count', default=0, dest='verbose')
    verbose.add_argument('--verbosity',
                          help=('Show debug messages'),
                          type=int, dest='verbose')
    argParser.set_defaults(DEBUG=False)


    return argParser.parse_args()
