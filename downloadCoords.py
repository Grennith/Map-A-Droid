from db.dbWrapper import DbWrapper
from walkerArgs import parseArgs
import glob, os

args = parseArgs()

dbWrapper = DbWrapper(str(args.db_method), str(args.dbip), args.dbport, args.dbusername, args.dbpassword, args.dbname, args.timezone)


def main():
    if os.path.isfile(args.route_file + '.calc'):
        print("Found existing Route - deleting")
        os.remove(args.route_file + '.calc')
    if dbWrapper.downloadDbCoords():
        print("Successfully saved coords to %s" % str(args.file))
    else:
        print("Failed downloading gym coords")


if __name__ == '__main__':
    main()