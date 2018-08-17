from db.dbWrapper import DbWrapper
from walkerArgs import parseArgs

args = parseArgs()

dbWrapper = DbWrapper(str(args.db_method), str(args.dbip), args.dbport, args.dbusername, args.dbpassword, args.dbname, args.timezone)


def main():
    if dbWrapper.downloadGymImages():
        print("Successfully downloaded gym images to gym_img")
    else:
        print("Failed downloading gym images")


if __name__ == '__main__':
    main()